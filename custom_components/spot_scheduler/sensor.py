"""Sensor platform for SpotScheduler."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change

import homeassistant.util.dt as dt_util

from .const import DOMAIN, CONF_DEVICES, CONF_DEFAULT_STATE, DEFAULT_DEFAULT_STATE

if __name__ != "__main__":
    from . import SpotSchedulerConfigEntry, SpotSchedulerData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SpotSchedulerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities = [SpotScheduleStatusSensor(entry)]
    async_add_entities(entities, True)

    # Remove stale sensor entities left over from previous versions
    # (SpotCurrentPriceSensor, SpotMinPriceSensor, SpotMaxPriceSensor)
    ent_reg = er.async_get(hass)
    current_unique_ids = {e.unique_id for e in entities}
    stale = [
        e for e in ent_reg.entities.values()
        if e.config_entry_id == entry.entry_id
        and e.platform == DOMAIN
        and e.domain == "sensor"
        and e.unique_id not in current_unique_ids
    ]
    for stale_entity in stale:
        _LOGGER.debug("Removing stale sensor entity: %s", stale_entity.entity_id)
        ent_reg.async_remove(stale_entity.entity_id)

    # Refresh status sensor when prices or schedules change
    status_sensor = entities[0]

    @callback
    def _on_prices_updated(event: Event) -> None:
        if event.data.get("entry_id") != entry.entry_id:
            return
        status_sensor.async_schedule_update_ha_state()

    @callback
    def _on_schedule_changed(event: Event) -> None:
        status_sensor.async_schedule_update_ha_state()

    entry.async_on_unload(
        hass.bus.async_listen(f"{DOMAIN}_prices_updated", _on_prices_updated)
    )
    entry.async_on_unload(
        hass.bus.async_listen(f"{DOMAIN}_schedule_changed", _on_schedule_changed)
    )


class _SpotBase(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: SpotSchedulerConfigEntry) -> None:
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.data.get("name", "SpotScheduler"),
            manufacturer="SpotScheduler",
            model="Spot Price Scheduler",
        )

    def _data(self) -> SpotSchedulerData | None:
        if self._entry.entry_id not in self.hass.data.get(DOMAIN, set()):
            return None
        return self._entry.runtime_data


class SpotScheduleStatusSensor(_SpotBase):
    def __init__(self, entry: SpotSchedulerConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_managed_devices"
        self._attr_name = "Managed devices"
        self._attr_icon = "mdi:devices"
        self._attr_native_unit_of_measurement = None
        self._attr_state_class = None

    @property
    def native_value(self) -> int:
        merged = {**self._entry.data, **self._entry.options}
        return len(merged.get(CONF_DEVICES, []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        today = dt_util.now().date().isoformat()
        data = self._data()
        if data is None:
            merged = {**self._entry.data, **self._entry.options}
            return {
                "schedules": {},
                "prices": {},
                "prices_all": {},
                "schedules_all": {},
                "min_price": None,
                "max_price": None,
                "tomorrow_fetched": False,
                "expensive_hours_count": merged.get("expensive_hours_count", 3),
                "auto_select_hours": merged.get("auto_select_hours", 0),
                "devices": merged.get("devices", []),
                "price_threshold_low": merged.get("price_threshold_low", 5.0),
                "price_threshold_high": merged.get("price_threshold_high", 15.0),
                "default_state": merged.get(CONF_DEFAULT_STATE, DEFAULT_DEFAULT_STATE),
            }
        # Merge options over data for current settings
        merged = {**self._entry.data, **self._entry.options}
        return {
            "schedules": data.schedules.get(today, {}),
            "prices":    data.prices.get(today, {}),
            # Filter out dates with < 20 hours — CET→local timezone
            # conversion can spill a single hour into an adjacent date.
            "prices_all": {
                date: hours
                for date, hours in data.prices.items()
                if len(hours) >= 20
            },
            "schedules_all": data.schedules,
            "min_price": data.min_price,
            "max_price": data.max_price,
            "tomorrow_fetched": data.tomorrow_fetched,
            "expensive_hours_count": merged.get("expensive_hours_count", 3),
            "auto_select_hours": merged.get("auto_select_hours", 0),
            "devices": merged.get("devices", []),
            "price_threshold_low": merged.get("price_threshold_low", 5.0),
            "price_threshold_high": merged.get("price_threshold_high", 15.0),
            "default_state": merged.get(CONF_DEFAULT_STATE, DEFAULT_DEFAULT_STATE),
        }
