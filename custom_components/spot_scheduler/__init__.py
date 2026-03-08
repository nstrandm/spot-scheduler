"""SpotScheduler – schedule devices by Nord Pool spot prices (HA core integration)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, date, timedelta

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback, Event
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.helpers.storage import Store
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util

from .const import (
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
    CARD_VERSION,
    NORDPOOL_DOMAIN,
    CONF_NORDPOOL_CONFIG_ENTRY,
    CONF_DEVICES,
    CONF_AUTO_SELECT_HOURS,
    CONF_EXPENSIVE_HOURS_COUNT,
    CONF_AUTO_SELECT_ENABLED,
    CONF_BLOCK_EXPENSIVE_HOURS,
    DEFAULT_AUTO_SELECT_HOURS,
    DEFAULT_AUTO_SELECT_ENABLED,
    DEFAULT_EXPENSIVE_HOURS,
    DEFAULT_BLOCK_EXPENSIVE,
    ISSUE_NORDPOOL_MISSING,
    ISSUE_NORDPOOL_UNAVAILABLE,
    TOMORROW_POLL_INTERVAL_MINUTES,
    TOMORROW_POLL_START_HOUR,
)
from .logic import parse_hourly_prices, prune_old_dates, set_schedule, cheapest_hours, expensive_hours

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.SENSOR, Platform.NUMBER]


def _get_nordpool_entry_id(entry: ConfigEntry) -> str | None:
    """Get Nord Pool config entry ID, preferring options over data."""
    return (
        entry.options.get(CONF_NORDPOOL_CONFIG_ENTRY)
        or entry.data.get(CONF_NORDPOOL_CONFIG_ENTRY)
    )

SET_SCHEDULE_SCHEMA = vol.Schema({
    vol.Optional("date"): cv.date,
    vol.Required("hour"): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
    vol.Required("device_id"): cv.entity_id,
    vol.Optional("enabled"): cv.boolean,  # absent/null = unset (don't touch)
})

REFRESH_PRICES_SCHEMA = vol.Schema({
    vol.Optional("date"): cv.date,
})

APPLY_NOW_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
})


# ── Setup / Unload ─────────────────────────────────────────────────────────────

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SpotScheduler from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Register the Lovelace card JS resource (once, idempotent)
    await _register_frontend(hass)

    nordpool_entry_id = _get_nordpool_entry_id(entry)
    if not hass.config_entries.async_get_entry(nordpool_entry_id):
        ir.async_create_issue(
            hass, DOMAIN, ISSUE_NORDPOOL_MISSING,
            is_fixable=False, severity=ir.IssueSeverity.ERROR,
            translation_key="nordpool_integration_missing",
            translation_placeholders={"entry_id": nordpool_entry_id or "unknown"},
        )
        _LOGGER.error("Nord Pool config entry %s not found.", nordpool_entry_id)
        return False

    ir.async_delete_issue(hass, DOMAIN, ISSUE_NORDPOOL_MISSING)
    ir.async_delete_issue(hass, DOMAIN, ISSUE_NORDPOOL_UNAVAILABLE)

    store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry.entry_id}")
    stored = await store.async_load() or {}

    _merged_cfg = {**entry.data, **entry.options}
    loaded_prices: dict = stored.get("prices", {})
    today_str = dt_util.now().date().isoformat()
    today_price_vals = list(loaded_prices.get(today_str, {}).values())

    hass.data[DOMAIN][entry.entry_id] = {
        "config":     entry.data,
        "store":      store,
        "schedules":  stored.get("schedules", {}),
        "prices":     loaded_prices,
        "min_price":  min(today_price_vals) if today_price_vals else None,
        "max_price":  max(today_price_vals) if today_price_vals else None,
        "tomorrow_fetched": False,   # guard: fetch tomorrow at most once per day
        "_tomorrow_lock":  asyncio.Lock(),  # prevents concurrent fetches
        "_unload_callbacks": [],
        # Track which devices were configured at setup time so the update_listener
        # can avoid a full reload when only number-entity options change.
        "configured_devices": set(_merged_cfg.get(CONF_DEVICES, [])),
    }

    # Fetch today's prices once on startup; warn via Repairs if it fails
    ok = await _fetch_prices_for_date(hass, entry, dt_util.now().date())
    if not ok:
        _maybe_raise_unavailable_issue(hass)

    # Also try tomorrow's prices on startup if it's past poll start hour
    if dt_util.now().hour >= TOMORROW_POLL_START_HOUR:
        tomorrow = dt_util.now().date() + timedelta(days=1)
        tok = await _fetch_prices_for_date(hass, entry, tomorrow)
        if tok:
            hass.data[DOMAIN][entry.entry_id]["tomorrow_fetched"] = True
            _LOGGER.info("Tomorrow's prices fetched on startup (%s)", tomorrow)

    # Watch every Nord Pool entity belonging to this config entry.
    # When next_price (or any sensor) updates its state, Nord Pool has polled
    # a fresh data set – use that as a lightweight signal to try tomorrow.
    _setup_nordpool_tracking(hass, entry, nordpool_entry_id)

    # Polled fallback: one listener, fires every 15 min after TOMORROW_POLL_START_HOUR.
    # Core Nord Pool has no tomorrow_valid attribute, so we poll get_prices_for_date.
    # The call is cheap because HA caches the result internally.
    poll_minutes = list(range(0, 60, TOMORROW_POLL_INTERVAL_MINUTES))  # [0, 15, 30, 45]

    @callback
    def _poll_tomorrow_cb(_now) -> None:
        hass.async_create_task(_poll_tomorrow_if_needed(hass, entry))

    cancel_poll = async_track_time_change(
        hass,
        _poll_tomorrow_cb,
        hour=list(range(TOMORROW_POLL_START_HOUR, 24)),
        minute=poll_minutes,
        second=30,
    )
    hass.data[DOMAIN][entry.entry_id]["_unload_callbacks"].append(cancel_poll)

    # Midnight: new day → reset guard, re-fetch, prune old data
    @callback
    def _midnight_cb(_now) -> None:
        hass.async_create_task(_on_midnight(hass, entry))

    cancel_midnight = async_track_time_change(
        hass,
        _midnight_cb,
        hour=0, minute=0, second=15,
    )
    hass.data[DOMAIN][entry.entry_id]["_unload_callbacks"].append(cancel_midnight)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _register_services(hass, entry)

    _LOGGER.info("SpotScheduler started (Nord Pool entry: %s)", nordpool_entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload SpotScheduler cleanly."""
    data = hass.data[DOMAIN].get(entry.entry_id, {})
    for cancel in data.get("_unload_callbacks", []):
        cancel()

    # Only remove services when the last instance is unloaded
    remaining = [e for e in hass.data[DOMAIN] if e != entry.entry_id]
    if not remaining:
        for svc in ("set_device_schedule", "refresh_prices", "apply_schedules_now"):
            if hass.services.has_service(DOMAIN, svc):
                hass.services.async_remove(DOMAIN, svc)

    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload only when the device list changes.

    Number-entity and switch option writes (price thresholds, expensive_hours,
    auto_select_enabled, etc.) also trigger this listener, but those should NOT
    cause a full reload — the entities read entry.options dynamically.
    """
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    configured: set = data.get("configured_devices", set())
    current = set({**entry.data, **entry.options}.get(CONF_DEVICES, []))
    if configured != current:
        _LOGGER.info(
            "SpotScheduler: device list changed (%s → %s), reloading.",
            configured, current,
        )
        await hass.config_entries.async_reload(entry.entry_id)


# ── Frontend resource registration ─────────────────────────────────────────────

CARD_URL = f"/api/{DOMAIN}/static/spot-scheduler-card.js?v={CARD_VERSION}"

async def _register_frontend(hass: HomeAssistant) -> None:
    """Register the static HTTP path (once) and keep the Lovelace resource URL current.

    HACS serves integration files under custom_components/, not /hacsfiles/.
    We register a static path ourselves so the card works regardless of
    whether the integration was installed via HACS or manually.

    The static-path registration is guarded to run only once per HA process
    (re-registering the same path raises an error).  The Lovelace resource
    URL check runs on every call so version bumps and first-time registrations
    are handled even when Lovelace was not ready at the first startup attempt.
    """
    # ── Static HTTP path (once per HA process) ─────────────────────────────
    if not hass.data.get(f"{DOMAIN}_static_registered"):
        import pathlib
        static_path = str(pathlib.Path(__file__).parent / "www")
        static_url  = f"/api/{DOMAIN}/static"

        try:
            from homeassistant.components.http import StaticPathConfig
            await hass.http.async_register_static_paths(
                [StaticPathConfig(static_url, static_path, True)]
            )
        except (ImportError, AttributeError):
            try:
                hass.http.register_static_path(static_url, static_path, cache_headers=True)
            except Exception as exc:
                _LOGGER.warning("Could not register static path: %s", exc)

        hass.data[f"{DOMAIN}_static_registered"] = True

    # ── Lovelace resource URL (every call – idempotent) ────────────────────
    try:
        from homeassistant.components.lovelace.resources import (
            ResourceStorageCollection,
        )
        resources: ResourceStorageCollection | None = hass.data.get("lovelace_resources")
        if resources is not None:
            existing = [
                r for r in resources.async_items()
                if DOMAIN in r.get("url", "")
            ]
            if not existing:
                await resources.async_create_item({"res_type": "module", "url": CARD_URL})
                _LOGGER.info("Registered Lovelace resource: %s", CARD_URL)
            elif existing[0].get("url") != CARD_URL:
                # Version changed – update the registered URL so browsers fetch the new file
                await resources.async_update_item(
                    existing[0]["id"], {"res_type": "module", "url": CARD_URL}
                )
                _LOGGER.info("Updated Lovelace resource URL to: %s", CARD_URL)
            else:
                _LOGGER.debug("Lovelace resource already up-to-date: %s", CARD_URL)
        else:
            _LOGGER.debug(
                "Lovelace resources collection not available yet – "
                "will be registered on next reload or HA restart."
            )
    except Exception as exc:
        _LOGGER.debug("Could not auto-register Lovelace resource: %s", exc)


# ── Nord Pool state tracking ───────────────────────────────────────────────────

def _setup_nordpool_tracking(
    hass: HomeAssistant, entry: ConfigEntry, nordpool_entry_id: str
) -> None:
    """
    Watch all Nord Pool entities for this config entry.

    Core Nord Pool does NOT expose a tomorrow_valid attribute.
    Instead we watch for any state change on its sensors – this fires every
    15 min (since HA 2026.x) or every hour.  On each change we opportunistically
    try to fetch tomorrow's prices if we haven't yet.
    """
    ent_reg = er.async_get(hass)
    nordpool_entities = [
        e.entity_id
        for e in ent_reg.entities.values()
        if e.config_entry_id == nordpool_entry_id
    ]

    if not nordpool_entities:
        _LOGGER.warning(
            "No Nord Pool entities found for entry %s – "
            "will rely on scheduled polling only.",
            nordpool_entry_id,
        )
        return

    @callback
    def _on_nordpool_update(event: Event) -> None:
        """On any Nord Pool sensor change, opportunistically try tomorrow."""
        hass.async_create_task(_poll_tomorrow_if_needed(hass, entry))

    cancel = async_track_state_change_event(
        hass, nordpool_entities, _on_nordpool_update
    )
    hass.data[DOMAIN][entry.entry_id]["_unload_callbacks"].append(cancel)
    _LOGGER.debug("Tracking %d Nord Pool entities for entry %s", len(nordpool_entities), nordpool_entry_id)


async def _poll_tomorrow_if_needed(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """
    Fetch tomorrow's prices if not already fetched today.
    An asyncio.Lock prevents concurrent fetches when the Nord Pool sensor
    update event and the scheduled poll fire at the same moment.
    """
    if entry.entry_id not in hass.data.get(DOMAIN, {}):
        return

    data = hass.data[DOMAIN][entry.entry_id]

    # Fast-path checks outside the lock to avoid unnecessary contention
    if data.get("tomorrow_fetched"):
        _LOGGER.debug("Tomorrow already fetched, skipping poll")
        return
    if dt_util.now().hour < TOMORROW_POLL_START_HOUR:
        _LOGGER.debug("Too early to poll tomorrow (hour=%d, start=%d)", dt_util.now().hour, TOMORROW_POLL_START_HOUR)
        return

    lock: asyncio.Lock = data["_tomorrow_lock"]
    if lock.locked():
        return   # another coroutine is already fetching

    async with lock:
        # Re-check inside the lock – another coroutine may have succeeded
        if data.get("tomorrow_fetched"):
            return

        tomorrow = dt_util.now().date() + timedelta(days=1)
        if tomorrow.isoformat() in data.get("prices", {}):
            data["tomorrow_fetched"] = True
            return

        ok = await _fetch_prices_for_date(hass, entry, tomorrow)
        if ok:
            data["tomorrow_fetched"] = True
            _LOGGER.info("Tomorrow's prices fetched successfully (%s)", tomorrow)


# ── Midnight handler ───────────────────────────────────────────────────────────

async def _on_midnight(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """New day: prune stale data, reset tomorrow guard, fetch today."""
    await _daily_reset(hass, entry)

    if entry.entry_id not in hass.data.get(DOMAIN, {}):
        return  # entry was unloaded during reset

    # Reset guard so tomorrow (now today+1) will be fetched again tonight
    hass.data[DOMAIN][entry.entry_id]["tomorrow_fetched"] = False

    ok = await _fetch_prices_for_date(hass, entry, dt_util.now().date())
    if not ok and entry.entry_id in hass.data.get(DOMAIN, {}):
        _maybe_raise_unavailable_issue(hass)


# ── Price fetching ─────────────────────────────────────────────────────────────

async def _fetch_prices_for_date(
    hass: HomeAssistant, entry: ConfigEntry, target_date: date
) -> bool:
    """
    Call nordpool.get_prices_for_date and store hourly averages.
    Returns True on success, False on any failure.
    """
    if entry.entry_id not in hass.data.get(DOMAIN, {}):
        return False

    nordpool_entry_id = _get_nordpool_entry_id(entry)
    date_str = target_date.isoformat()

    _LOGGER.debug(
        "Fetching prices: nordpool entry=%s, date=%s",
        nordpool_entry_id, date_str,
    )

    try:
        result = await hass.services.async_call(
            NORDPOOL_DOMAIN,
            "get_prices_for_date",
            {"config_entry": nordpool_entry_id, "date": date_str},
            blocking=True,
            return_response=True,
        )
    except Exception as exc:
        _LOGGER.warning(
            "nordpool.get_prices_for_date failed for %s (entry=%s): %s",
            date_str, nordpool_entry_id, exc,
        )
        return False

    if not result:
        _LOGGER.warning("Empty response from nordpool for %s (entry=%s)", date_str, nordpool_entry_id)
        return False

    _LOGGER.debug("Nord Pool raw response keys: %s", list(result.keys()) if isinstance(result, dict) else type(result))

    # Parse: { area_code: [ {start, end, price}, … ] }
    # 15-min slots are averaged into hourly buckets via logic.parse_hourly_prices.
    tz = dt_util.get_time_zone(hass.config.time_zone)
    averaged: dict[int, float] = {}
    try:
        for area_data in result.values():
            if not isinstance(area_data, list):
                continue
            parsed = parse_hourly_prices(area_data, tz)
            # Merge (in practice there's usually one area per entry)
            for h, p in parsed.items():
                averaged[h] = p
    except Exception as exc:
        _LOGGER.error("Failed to parse Nord Pool price data for %s: %s", date_str, exc)
        return False

    if not averaged:
        _LOGGER.debug("No usable price slots in Nord Pool response for %s", date_str)
        return False

    prices_list = list(averaged.values())

    if entry.entry_id not in hass.data.get(DOMAIN, {}):
        return False   # entry was unloaded while we awaited

    data = hass.data[DOMAIN][entry.entry_id]

    # Prices are new if this date wasn't already in the store (loaded from
    # persistent storage at startup).  Re-fetching known prices on HA restart
    # should NOT re-trigger auto-select — it already ran when prices first arrived.
    prices_are_new = date_str not in data["prices"]

    data["prices"][date_str] = averaged

    if date_str == dt_util.now().date().isoformat():
        data["min_price"] = min(prices_list)
        data["max_price"] = max(prices_list)

    # Clear any outstanding Repairs issue
    ir.async_delete_issue(hass, DOMAIN, ISSUE_NORDPOOL_UNAVAILABLE)

    _LOGGER.debug("Stored %d hourly prices for %s", len(averaged), date_str)
    hass.bus.async_fire(
        f"{DOMAIN}_prices_updated",
        {"entry_id": entry.entry_id, "date": date_str},
    )

    # Auto-select cheapest / block expensive only when prices arrive for the
    # first time for this date.  Skipping on restart prevents mid-hour device
    # state changes caused by re-running the schedule logic on stale data.
    if prices_are_new:
        await _auto_select_cheapest(hass, entry, date_str)

    return True


def _maybe_raise_unavailable_issue(hass: HomeAssistant) -> None:
    ir.async_create_issue(
        hass, DOMAIN, ISSUE_NORDPOOL_UNAVAILABLE,
        is_fixable=True, severity=ir.IssueSeverity.WARNING,
        translation_key="nordpool_unavailable",
        translation_placeholders={},
    )


# ── Daily cleanup ──────────────────────────────────────────────────────────────

async def _daily_reset(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Prune schedules and prices older than yesterday."""
    if entry.entry_id not in hass.data.get(DOMAIN, {}):
        return
    yesterday = dt_util.now().date() - timedelta(days=1)
    data = hass.data[DOMAIN][entry.entry_id]
    for bucket in ("schedules", "prices"):
        prune_old_dates(data.get(bucket, {}), yesterday)
    await _save_schedules(hass, entry)
    _LOGGER.debug("Midnight cleanup complete.")


async def _save_schedules(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Persist schedules and prices to HA storage (included in HA backups)."""
    if entry.entry_id not in hass.data.get(DOMAIN, {}):
        return
    data = hass.data[DOMAIN][entry.entry_id]
    await data["store"].async_save({
        "schedules": data.get("schedules", {}),
        "prices":    data.get("prices", {}),
    })


# ── Auto-select cheapest hours ─────────────────────────────────────────────────

async def _auto_select_cheapest(
    hass: HomeAssistant, entry: ConfigEntry, date_str: str
) -> None:
    """Auto-configure hours after prices arrive.

    1. Set cheapest N hours to ON for each device (if not already scheduled).
    2. If "block expensive hours" is enabled, set top N expensive hours to OFF
       for each device (unless they were just set to ON by step 1).

    Skips devices that already have any schedule entry for the given date.
    """
    if entry.entry_id not in hass.data.get(DOMAIN, {}):
        return

    data   = hass.data[DOMAIN][entry.entry_id]
    merged = {**entry.data, **entry.options}

    prices = data.get("prices", {}).get(date_str, {})
    if not prices:
        return

    devices   = merged.get(CONF_DEVICES, [])
    schedules = data.setdefault("schedules", {})
    changed   = False

    # Resolve auto_select_hours – may be legacy int or new per-device dict
    raw_auto = merged.get(CONF_AUTO_SELECT_HOURS, DEFAULT_AUTO_SELECT_HOURS)
    if isinstance(raw_auto, int):
        auto_hours: dict[str, int] = {d: raw_auto for d in devices}
    else:
        auto_hours = raw_auto if isinstance(raw_auto, dict) else {}

    # Step 1: auto-select cheapest hours (skip if globally disabled)
    auto_select_enabled = merged.get(CONF_AUTO_SELECT_ENABLED, DEFAULT_AUTO_SELECT_ENABLED)
    for device_id in devices:
        if not auto_select_enabled:
            break
        n = int(auto_hours.get(device_id, 0))
        if n <= 0:
            continue
        device_sched = schedules.get(date_str, {}).get(device_id)
        if device_sched is not None and len(device_sched) > 0:
            continue
        cheap = cheapest_hours(prices, n)
        schedules.setdefault(date_str, {}).setdefault(device_id, {})
        for hour in cheap:
            schedules[date_str][device_id][str(hour)] = True
        changed = True
        _LOGGER.info(
            "Auto-select: set %d cheapest hours for %s on %s",
            n, device_id, date_str,
        )

    # Step 2: block expensive hours (if option is enabled)
    if merged.get(CONF_BLOCK_EXPENSIVE_HOURS, DEFAULT_BLOCK_EXPENSIVE):
        exp_count = int(merged.get(CONF_EXPENSIVE_HOURS_COUNT, DEFAULT_EXPENSIVE_HOURS))
        if exp_count > 0:
            exp_hrs = expensive_hours(prices, exp_count)

            # For today, never retroactively block the current or past hours.
            # _apply_schedules fires right after startup and would otherwise
            # immediately turn a device off mid-hour.
            now = dt_util.now()
            today_str = now.date().isoformat()
            min_hour = (now.hour + 1) if date_str == today_str else 0

            blockable = [h for h in exp_hrs if h >= min_hour]
            for device_id in devices:
                for hour in blockable:
                    existing = schedules.get(date_str, {}).get(device_id, {}).get(str(hour))
                    if existing is not True:  # don't overwrite auto-selected ON
                        set_schedule(schedules, date_str, device_id, hour, False)
                        changed = True
            _LOGGER.info(
                "Block expensive: set %d expensive hours (h>=%d) to OFF on %s",
                len(blockable), min_hour, date_str,
            )

    if changed:
        await _save_schedules(hass, entry)
        hass.bus.async_fire(f"{DOMAIN}_schedule_changed", {
            "device_id": None, "date": date_str, "hour": None, "enabled": None,
        })


# ── Services ───────────────────────────────────────────────────────────────────

def _register_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register services once; safe to call again on additional instances."""

    async def set_device_schedule(call: ServiceCall) -> None:
        target_date = (call.data.get("date") or dt_util.now().date()).isoformat()
        hour: int        = call.data["hour"]
        device_id: str   = call.data["device_id"]
        enabled: bool | None = call.data.get("enabled")  # None = unset / don't touch

        matched = False
        for eid, data in hass.data.get(DOMAIN, {}).items():
            if not isinstance(data, dict):
                continue
            # Check both config data and options (options flow stores
            # updated device list in options, not data)
            cfg_entry = hass.config_entries.async_get_entry(eid)
            devices = (
                (cfg_entry.options.get(CONF_DEVICES) if cfg_entry else None)
                or data.get("config", {}).get(CONF_DEVICES, [])
            )
            if device_id not in devices:
                continue
            matched = True
            set_schedule(
                data.setdefault("schedules", {}),
                target_date, device_id, hour, enabled,
            )
            if cfg_entry:
                await _save_schedules(hass, cfg_entry)

        if not matched:
            _LOGGER.warning(
                "set_device_schedule: device '%s' is not managed by any SpotScheduler entry. "
                "Check your configuration.",
                device_id,
            )
            return

        hass.bus.async_fire(f"{DOMAIN}_schedule_changed", {
            "device_id": device_id, "date": target_date,
            "hour": hour, "enabled": enabled,
        })

    async def refresh_prices(call: ServiceCall) -> None:
        target_date = call.data.get("date") or dt_util.now().date()
        if isinstance(target_date, str):
            target_date = date.fromisoformat(target_date)
        for eid in list(hass.data.get(DOMAIN, {}).keys()):
            cfg = hass.config_entries.async_get_entry(eid)
            if cfg:
                ok = await _fetch_prices_for_date(hass, cfg, target_date)
                if not ok and target_date == dt_util.now().date():
                    _maybe_raise_unavailable_issue(hass)

    if not hass.services.has_service(DOMAIN, "set_device_schedule"):
        hass.services.async_register(
            DOMAIN, "set_device_schedule", set_device_schedule,
            schema=SET_SCHEDULE_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, "refresh_prices"):
        hass.services.async_register(
            DOMAIN, "refresh_prices", refresh_prices,
            schema=REFRESH_PRICES_SCHEMA,
        )

    async def apply_schedules_now(call: ServiceCall) -> None:
        entry_id = call.data.get("entry_id")
        hass.bus.async_fire(f"{DOMAIN}_apply_now", {"entry_id": entry_id})
        _LOGGER.info(
            "apply_schedules_now triggered manually (entry_id=%s)",
            entry_id or "all",
        )

    if not hass.services.has_service(DOMAIN, "apply_schedules_now"):
        hass.services.async_register(
            DOMAIN, "apply_schedules_now", apply_schedules_now,
            schema=APPLY_NOW_SCHEMA,
        )
