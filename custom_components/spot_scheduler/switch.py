"""Switch platform for SpotScheduler – config switches and scheduled device control."""
from __future__ import annotations

import logging

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
    CONF_DEFAULT_STATE,
    DEFAULT_DEFAULT_STATE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    devices: list[str] = (
        entry.options.get("devices")
        or entry.data.get("devices", [])
    )

    config_switches = [SpotAutoSelectSwitch(entry), SpotBlockExpensiveSwitch(entry)]
    async_add_entities(config_switches, True)

    # Remove stale switch entities (e.g. old per-device schedule switches)
    ent_reg = er.async_get(hass)
    current_unique_ids = {s.unique_id for s in config_switches}
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
        hass.async_create_task(_apply_schedules(hass, entry, devices))

    cancel = async_track_time_change(hass, _hour_cb, minute=0, second=5)
    entry.async_on_unload(cancel)

    # Apply current hour's schedule once HA is fully started
    if hass.is_running:
        await _apply_schedules(hass, entry, devices)
    else:
        @callback
        def _started_cb(_event) -> None:
            hass.async_create_task(_apply_schedules(hass, entry, devices))

        entry.async_on_unload(
            hass.bus.async_listen_once("homeassistant_started", _started_cb)
        )

    # Apply immediately if a schedule change affects the current hour
    @callback
    def _on_schedule_changed(event: Event) -> None:
        now = dt_util.now()
        today = now.date().isoformat()
        if event.data.get("date") == today and event.data.get("hour") == now.hour:
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
        hass.async_create_task(_apply_schedules(hass, entry, devices))

    entry.async_on_unload(
        hass.bus.async_listen(f"{DOMAIN}_apply_now", _on_apply_now)
    )


async def _apply_schedule_for_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device_id: str | None,
    enabled: bool | str | None,
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
        _LOGGER.info("Schedule (immediate): ON   %s", device_id)
    elif enabled is False:
        await hass.services.async_call(
            domain, "turn_off", {}, blocking=False,
            target={"entity_id": device_id},
        )
        _LOGGER.info("Schedule (immediate): OFF  %s", device_id)
    else:
        # None = use default, "skip" = explicit don't touch — both leave device as-is here
        _LOGGER.debug("Schedule (immediate): skip %s (%s)", device_id, enabled)


async def _apply_schedules(
    hass: HomeAssistant,
    entry: ConfigEntry,
    devices: list[str],
) -> None:
    """Turn devices on/off per schedule at the top of each hour.

    State semantics:
      True  → turn on
      False → turn off
      None  → apply default_state setting (on / off / dont_touch)
    """
    if entry.entry_id not in hass.data.get(DOMAIN, {}):
        _LOGGER.warning("_apply_schedules: entry %s not in hass.data, skipping", entry.entry_id)
        return

    now     = dt_util.now()
    today   = now.date().isoformat()
    hour    = now.hour
    sched   = hass.data[DOMAIN][entry.entry_id].get("schedules", {})
    today_s = sched.get(today, {})

    merged = {**entry.data, **entry.options}
    default_state = merged.get(CONF_DEFAULT_STATE, DEFAULT_DEFAULT_STATE)

    _LOGGER.debug(
        "_apply_schedules fired: date=%s hour=%d devices=%d default_state=%s",
        today, hour, len(devices), default_state,
    )

    for dev in devices:
        state = today_s.get(dev, {}).get(str(hour))

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
        elif state == "skip":
            # Explicit don't touch — overrides default_state
            _LOGGER.debug("Schedule: skip %s  h=%d (explicit)", dev, hour)
        elif default_state == "on":
            await hass.services.async_call(
                domain, "turn_on", {}, blocking=False,
                target={"entity_id": dev},
            )
            _LOGGER.info("Schedule: ON   %s  h=%d (default)", dev, hour)
        elif default_state == "off":
            await hass.services.async_call(
                domain, "turn_off", {}, blocking=False,
                target={"entity_id": dev},
            )
            _LOGGER.info("Schedule: OFF  %s  h=%d (default)", dev, hour)
        else:
            _LOGGER.debug("Schedule: skip %s  h=%d (don't touch)", dev, hour)


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
