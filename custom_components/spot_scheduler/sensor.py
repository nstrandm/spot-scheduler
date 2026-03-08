"""Sensor platform for SpotScheduler."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change

import homeassistant.util.dt as dt_util

from .const import DOMAIN
from .logic import count_enabled_slots

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities = [SpotScheduleStatusSensor(hass, entry)]
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

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.data.get("name", "SpotScheduler"),
            "manufacturer": "SpotScheduler",
            "model": "Spot Price Scheduler",
        }

    def _data(self) -> dict:
        return self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})


class SpotScheduleStatusSensor(_SpotBase):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_unique_id = f"{entry.entry_id}_schedule_status"
        self._attr_name = "Schedule status"
        self._attr_icon = "mdi:calendar-clock"
        # "slots" is not an HA-standard unit; omit unit and state_class so
        # HA doesn't try to graph this as a measurement or add it to energy stats.
        self._attr_native_unit_of_measurement = None
        self._attr_state_class = None

    @property
    def native_value(self) -> int:
        today = dt_util.now().date().isoformat()
        return count_enabled_slots(self._data().get("schedules", {}), today)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        today = dt_util.now().date().isoformat()
        d = self._data()
        config = d.get("config", {})
        # Merge options over data for current settings
        merged = {**config, **self._entry.options}
        return {
            "schedules": d.get("schedules", {}).get(today, {}),
            "prices":    d.get("prices", {}).get(today, {}),
            "prices_tomorrow": d.get("prices", {}).get(
                (dt_util.now().date() + timedelta(days=1)).isoformat(), {}
            ),
            "schedules_tomorrow": d.get("schedules", {}).get(
                (dt_util.now().date() + timedelta(days=1)).isoformat(), {}
            ),
            "prices_yesterday": d.get("prices", {}).get(
                (dt_util.now().date() - timedelta(days=1)).isoformat(), {}
            ),
            "schedules_yesterday": d.get("schedules", {}).get(
                (dt_util.now().date() - timedelta(days=1)).isoformat(), {}
            ),
            "min_price": d.get("min_price"),
            "max_price": d.get("max_price"),
            "tomorrow_fetched": d.get("tomorrow_fetched", False),
            "expensive_hours_count": merged.get("expensive_hours_count", 3),
            "auto_select_hours": merged.get("auto_select_hours", 0),
            "devices": merged.get("devices", []),
            "price_threshold_low": merged.get("price_threshold_low", 5.0),
            "price_threshold_high": merged.get("price_threshold_high", 15.0),
        }
