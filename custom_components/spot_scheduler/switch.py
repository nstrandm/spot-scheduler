"""Switch platform for SpotScheduler – schedule-based virtual device switches."""
from __future__ import annotations

import logging
from datetime import datetime, date

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers import entity_registry as er

import homeassistant.util.dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    # Options override data when devices are changed via options flow
    devices: list[str] = (
        entry.options.get("devices")
        or entry.data.get("devices", [])
    )

    switches = [SpotDeviceScheduleSwitch(hass, entry, dev) for dev in devices]
    async_add_entities(switches, True)

    # Remove entity-registry entries for devices that were deleted via options flow
    ent_reg = er.async_get(hass)
    current_unique_ids = {s.unique_id for s in switches}
    stale = [
        e for e in ent_reg.entities.values()
        if e.config_entry_id == entry.entry_id
        and e.platform == DOMAIN
        and e.domain == "switch"
        and e.unique_id not in current_unique_ids
    ]
    for stale_entity in stale:
        _LOGGER.debug("Removing stale switch entity: %s", stale_entity.entity_id)
        ent_reg.async_remove(stale_entity.entity_id)

    # Apply scheduled states at the start of every hour (:00:30)
    cancel = async_track_time_change(
        hass,
        lambda _: hass.async_create_task(_apply_schedules(hass, entry, switches)),
        minute=0, second=30,
    )
    # Register via entry.async_on_unload so it is always cleaned up,
    # even if _unload_callbacks hasn't been populated yet (race guard).
    entry.async_on_unload(cancel)

    # Update switch states when schedule changes, and apply immediately
    # if the change affects the current hour
    @callback
    def _on_schedule_changed(event: Event) -> None:
        for sw in switches:
            sw.async_write_ha_state()

        # If the change is for today + current hour, apply it right away
        now = dt_util.now()
        today = now.date().isoformat()
        ev_date = event.data.get("date")
        ev_hour = event.data.get("hour")
        if ev_date == today and ev_hour == now.hour:
            hass.async_create_task(
                _apply_schedule_for_device(
                    hass, entry,
                    event.data.get("device_id"),
                    event.data.get("enabled"),
                )
            )

    entry.async_on_unload(
        hass.bus.async_listen(f"{DOMAIN}_schedule_changed", _on_schedule_changed)
    )


async def _apply_schedule_for_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device_id: str | None,
    enabled: bool | None,
) -> None:
    """Immediately apply a schedule change for a single device."""
    if not device_id or enabled is None:
        return
    if entry.entry_id not in hass.data.get(DOMAIN, {}):
        return

    if enabled:
        await hass.services.async_call(
            "homeassistant", "turn_on", {"entity_id": device_id}, blocking=False
        )
        _LOGGER.info("Schedule (immediate): ON  %s", device_id)
    else:
        await hass.services.async_call(
            "homeassistant", "turn_off", {"entity_id": device_id}, blocking=False
        )
        _LOGGER.info("Schedule (immediate): OFF %s", device_id)


async def _apply_schedules(
    hass: HomeAssistant,
    entry: ConfigEntry,
    switches: list[SpotDeviceScheduleSwitch],
) -> None:
    """Turn devices on/off per schedule at the top of each hour."""
    if entry.entry_id not in hass.data.get(DOMAIN, {}):
        return

    today   = dt_util.now().date().isoformat()
    hour    = dt_util.now().hour
    sched   = hass.data[DOMAIN][entry.entry_id].get("schedules", {})
    today_s = sched.get(today, {})

    for sw in switches:
        dev = sw.device_entity_id
        state = today_s.get(dev, {}).get(str(hour))

        if state is True:
            await hass.services.async_call(
                "homeassistant", "turn_on", {"entity_id": dev}, blocking=False
            )
            _LOGGER.info("Schedule: ON  %s  h=%d", dev, hour)
        elif state is False:
            await hass.services.async_call(
                "homeassistant", "turn_off", {"entity_id": dev}, blocking=False
            )
            _LOGGER.info("Schedule: OFF %s  h=%d", dev, hour)
        # None/unset → leave device as-is


class SpotDeviceScheduleSwitch(SwitchEntity):
    """
    Virtual switch per controlled device.

    State reflects whether the device is scheduled ON for the current hour.
    Toggling it sets the schedule for the current hour only.
    Actual device control happens in _apply_schedules() each hour.
    """

    _attr_has_entity_name = True
    _attr_icon            = "mdi:clock-outline"
    _attr_should_poll     = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        device_entity_id: str,
    ) -> None:
        self.hass = hass
        self._entry = entry
        self.device_entity_id = device_entity_id
        self._attr_unique_id  = f"{entry.entry_id}_schedule_{device_entity_id}"

        clean = device_entity_id.split(".")[-1].replace("_", " ").title()
        self._attr_name = f"Schedule: {clean}"

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.data.get("name", "SpotScheduler"),
        }

    @property
    def available(self) -> bool:
        """Mark unavailable if the target entity has been removed from HA."""
        return self.hass.states.get(self.device_entity_id) is not None

    @property
    def is_on(self) -> bool:
        data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        today = dt_util.now().date().isoformat()
        hour  = dt_util.now().hour
        return bool(
            data.get("schedules", {})
                .get(today, {})
                .get(self.device_entity_id, {})
                .get(str(hour), False)
        )

    @property
    def extra_state_attributes(self) -> dict:
        data  = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        today = dt_util.now().date().isoformat()
        return {
            "device_entity_id": self.device_entity_id,
            "today_schedule": (
                data.get("schedules", {})
                    .get(today, {})
                    .get(self.device_entity_id, {})
            ),
            "device_available": self.hass.states.get(self.device_entity_id) is not None,
        }

    async def async_turn_on(self, **kwargs) -> None:
        await self._set_current_hour(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set_current_hour(False)

    async def _set_current_hour(self, state: bool) -> None:
        await self.hass.services.async_call(
            DOMAIN, "set_device_schedule",
            {
                "date":      dt_util.now().date().isoformat(),
                "hour":      dt_util.now().hour,
                "device_id": self.device_entity_id,
                "enabled":   state,
            },
            blocking=True,   # wait until schedule is persisted before updating state
        )
        self.async_write_ha_state()
