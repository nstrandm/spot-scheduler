"""Sensor platform for SpotScheduler."""
from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback, Event
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
    current_price_sensor = SpotCurrentPriceSensor(hass, entry)
    status_sensor        = SpotScheduleStatusSensor(hass, entry)
    sensors = [
        current_price_sensor,
        SpotMinPriceSensor(hass, entry),
        SpotMaxPriceSensor(hass, entry),
        status_sensor,
    ]
    async_add_entities(sensors, True)

    # Push updates to sensors when prices arrive
    @callback
    def _on_prices_updated(event: Event) -> None:
        if event.data.get("entry_id") != entry.entry_id:
            return
        for s in sensors:
            s.async_schedule_update_ha_state()

    entry.async_on_unload(
        hass.bus.async_listen(f"{DOMAIN}_prices_updated", _on_prices_updated)
    )

    # Schedule changes only affect the status sensor – not price sensors
    @callback
    def _on_schedule_changed(event: Event) -> None:
        status_sensor.async_schedule_update_ha_state()

    entry.async_on_unload(
        hass.bus.async_listen(f"{DOMAIN}_schedule_changed", _on_schedule_changed)
    )

    # current_price sensor must refresh at the top of every hour even if no
    # other event fires (hour changes but prices/schedules stay the same)
    @callback
    def _on_new_hour(_now) -> None:
        for s in sensors:
            s.async_schedule_update_ha_state()

    entry.async_on_unload(
        async_track_time_change(hass, _on_new_hour, minute=0, second=5)
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

    def _today_prices(self) -> dict[int, float]:
        return self._data().get("prices", {}).get(dt_util.now().date().isoformat(), {})


class SpotCurrentPriceSensor(_SpotBase):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_unique_id = f"{entry.entry_id}_current_price"
        self._attr_name = "Current price"
        self._attr_native_unit_of_measurement = "EUR/kWh"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:lightning-bolt"

    @property
    def native_value(self) -> float | None:
        return self._today_prices().get(dt_util.now().hour)


class SpotMinPriceSensor(_SpotBase):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_unique_id = f"{entry.entry_id}_min_price"
        self._attr_name = "Min price today"
        self._attr_native_unit_of_measurement = "EUR/kWh"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:arrow-down-circle"

    @property
    def native_value(self) -> float | None:
        return self._data().get("min_price")


class SpotMaxPriceSensor(_SpotBase):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_unique_id = f"{entry.entry_id}_max_price"
        self._attr_name = "Max price today"
        self._attr_native_unit_of_measurement = "EUR/kWh"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:arrow-up-circle"

    @property
    def native_value(self) -> float | None:
        return self._data().get("max_price")


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
            "min_price": d.get("min_price"),
            "max_price": d.get("max_price"),
            "tomorrow_fetched": d.get("tomorrow_fetched", False),
            "expensive_hours_count": merged.get("expensive_hours_count", 3),
            "devices": merged.get("devices", []),
        }
