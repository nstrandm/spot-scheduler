"""Switch platform for SpotScheduler – schedule-based virtual device switches."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers import entity_registry as er

import homeassistant.util.dt as dt_util

from .const import (
    DOMAIN,
    CONF_AUTO_SELECT_ENABLED,
    DEFAULT_AUTO_SELECT_ENABLED,
    CONF_BLOCK_EXPENSIVE_HOURS,
    DEFAULT_BLOCK_EXPENSIVE,
)

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
    config_switches = [SpotAutoSelectSwitch(entry), SpotBlockExpensiveSwitch(entry)]
    all_entities = switches + config_switches
    async_add_entities(all_entities, True)

    # Remove entity-registry entries for devices that were deleted via options flow
    ent_reg = er.async_get(hass)
    current_unique_ids = {s.unique_id for s in all_entities}
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

    # Apply scheduled states at the start of every hour (:00:05)
    @callback
    def _hour_cb(_now) -> None:
        hass.async_create_task(_apply_schedules(hass, entry, switches))

    cancel = async_track_time_change(hass, _hour_cb, minute=0, second=5)
    entry.async_on_unload(cancel)

    # Apply current hour's schedule once HA is fully started
    if hass.is_running:
        await _apply_schedules(hass, entry, switches)
    else:
        @callback
        def _started_cb(_event) -> None:
            hass.async_create_task(_apply_schedules(hass, entry, switches))

        entry.async_on_unload(
            hass.bus.async_listen_once("homeassistant_started", _started_cb)
        )

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

    # Manual trigger for development / testing
    @callback
    def _on_apply_now(event: Event) -> None:
        target = event.data.get("entry_id")
        if target not in (None, entry.entry_id):
            return
        hass.async_create_task(_apply_schedules(hass, entry, switches))

    entry.async_on_unload(
        hass.bus.async_listen(f"{DOMAIN}_apply_now", _on_apply_now)
    )


async def _apply_schedule_for_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device_id: str | None,
    enabled: bool | None,
) -> None:
    """Immediately apply a schedule change for a single device."""
    if not device_id:
        return
    if entry.entry_id not in hass.data.get(DOMAIN, {}):
        return

    domain = device_id.split(".")[0]
    if enabled is True:
        await hass.services.async_call(
            domain, "turn_on", {}, blocking=False,
            target={"entity_id": device_id},
        )
        _LOGGER.info("Schedule (immediate): ON  %s", device_id)
    elif enabled is False:
        await hass.services.async_call(
            domain, "turn_off", {}, blocking=False,
            target={"entity_id": device_id},
        )
        _LOGGER.info("Schedule (immediate): OFF %s", device_id)
    else:
        # enabled is None = user unset the current hour → turn off
        await hass.services.async_call(
            domain, "turn_off", {}, blocking=False,
            target={"entity_id": device_id},
        )
        _LOGGER.info("Schedule (immediate): OFF (unset) %s", device_id)


async def _apply_schedules(
    hass: HomeAssistant,
    entry: ConfigEntry,
    switches: list[SpotDeviceScheduleSwitch],
) -> None:
    """Turn devices on/off per schedule at the top of each hour.

    State semantics:
      True  → turn on
      False → turn off
      None  → if previous hour was on, turn off; else don't touch
    """
    if entry.entry_id not in hass.data.get(DOMAIN, {}):
        _LOGGER.warning("_apply_schedules: entry %s not in hass.data, skipping", entry.entry_id)
        return

    now     = dt_util.now()
    today   = now.date().isoformat()
    hour    = now.hour
    sched   = hass.data[DOMAIN][entry.entry_id].get("schedules", {})
    today_s = sched.get(today, {})

    # Compute previous hour (may cross into yesterday)
    prev_hour = (hour - 1) % 24
    if hour == 0:
        prev_date = (now.date() - timedelta(days=1)).isoformat()
        prev_day_s = sched.get(prev_date, {})
    else:
        prev_day_s = today_s

    _LOGGER.debug(
        "_apply_schedules fired: date=%s hour=%d switches=%d",
        today, hour, len(switches),
    )

    for sw in switches:
        dev = sw.device_entity_id
        state      = today_s.get(dev, {}).get(str(hour))
        prev_state = prev_day_s.get(dev, {}).get(str(prev_hour))

        domain = dev.split(".")[0]
        if state is True:
            await hass.services.async_call(
                domain, "turn_on", {}, blocking=False,
                target={"entity_id": dev},
            )
            _LOGGER.info("Schedule: ON   %s  h=%d", dev, hour)
        elif state is False:
            await hass.services.async_call(
                domain, "turn_off", {}, blocking=False,
                target={"entity_id": dev},
            )
            _LOGGER.info("Schedule: OFF  %s  h=%d", dev, hour)
        elif prev_state is True:
            # Unset hour following an on-hour → release the device (turn off)
            await hass.services.async_call(
                domain, "turn_off", {}, blocking=False,
                target={"entity_id": dev},
            )
            _LOGGER.info("Schedule: OFF* %s  h=%d (end of on-sequence)", dev, hour)
        else:
            _LOGGER.debug("Schedule: skip %s  h=%d (unset, not following on)", dev, hour)


class SpotDeviceScheduleSwitch(SwitchEntity):
    """
    Virtual switch per controlled device.

    State reflects whether the device is scheduled ON for the current hour.
    Toggling it cycles: on → off → unset.
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
            blocking=True,
        )
        self.async_write_ha_state()


class SpotAutoSelectSwitch(SwitchEntity):
    """Config switch: enable/disable automatic cheapest-hours selection."""

    _attr_has_entity_name = True
    _attr_name            = "Cheapest hours auto-select"
    _attr_translation_key = "auto_select"
    _attr_icon            = "mdi:clock-check-outline"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_should_poll     = False

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_auto_select_enabled"

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.data.get("name", "SpotScheduler"),
        }

    @property
    def is_on(self) -> bool:
        return bool(
            {**self._entry.data, **self._entry.options}
            .get(CONF_AUTO_SELECT_ENABLED, DEFAULT_AUTO_SELECT_ENABLED)
        )

    async def async_turn_on(self, **kwargs) -> None:
        new_opts = {**self._entry.options, CONF_AUTO_SELECT_ENABLED: True}
        self.hass.config_entries.async_update_entry(self._entry, options=new_opts)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        new_opts = {**self._entry.options, CONF_AUTO_SELECT_ENABLED: False}
        self.hass.config_entries.async_update_entry(self._entry, options=new_opts)
        self.async_write_ha_state()


class SpotBlockExpensiveSwitch(SwitchEntity):
    """Config switch: when on, automatically set expensive hours to OFF when prices arrive."""

    _attr_has_entity_name = True
    _attr_name            = "Expensive hours turn off"
    _attr_translation_key = "block_expensive_hours"
    _attr_icon            = "mdi:fire-off"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_should_poll     = False

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_block_expensive_hours"

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.data.get("name", "SpotScheduler"),
        }

    @property
    def is_on(self) -> bool:
        return bool(
            {**self._entry.data, **self._entry.options}
            .get(CONF_BLOCK_EXPENSIVE_HOURS, DEFAULT_BLOCK_EXPENSIVE)
        )

    async def async_turn_on(self, **kwargs) -> None:
        new_opts = {**self._entry.options, CONF_BLOCK_EXPENSIVE_HOURS: True}
        self.hass.config_entries.async_update_entry(self._entry, options=new_opts)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        new_opts = {**self._entry.options, CONF_BLOCK_EXPENSIVE_HOURS: False}
        self.hass.config_entries.async_update_entry(self._entry, options=new_opts)
        self.async_write_ha_state()
