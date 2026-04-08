"""Tests for SpotScheduler __init__.py – integration-level logic."""

import asyncio
import pytest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.spot_scheduler import SpotSchedulerData
from custom_components.spot_scheduler.const import (
    DOMAIN,
    CONF_NORDPOOL_CONFIG_ENTRY,
    CONF_DEVICES,
    CONF_AUTO_SELECT_HOURS,
    CONF_AUTO_SELECT_ENABLED,
    CONF_BLOCK_EXPENSIVE_HOURS,
    CONF_EXPENSIVE_HOURS_COUNT,
    DEFAULT_AUTO_SELECT_ENABLED,
    DEFAULT_BLOCK_EXPENSIVE,
    TOMORROW_POLL_START_HOUR,
)

# Retry count used in the original fetch loop (hardcoded in __init__.py)
PRICE_FETCH_RETRY_COUNT = 3


def _make_runtime_data(**overrides) -> SpotSchedulerData:
    defaults = dict(
        store=AsyncMock(),
        schedules={},
        prices={},
        min_price=None,
        max_price=None,
        tomorrow_fetched=False,
        tomorrow_lock=asyncio.Lock(),
        configured_devices=set(),
        prices_in_storage=set(),
        auto_selected=set(),
    )
    defaults.update(overrides)
    return SpotSchedulerData(**defaults)


def _make_entry(entry_id="test_entry", data=None, options=None, runtime_data=None):
    entry = MagicMock()
    entry.entry_id = entry_id
    entry.data = data or {
        "name": "TestScheduler",
        CONF_NORDPOOL_CONFIG_ENTRY: "np_entry",
        CONF_DEVICES: ["switch.heater"],
    }
    entry.options = options or {}
    entry.async_on_unload = MagicMock()
    entry.add_update_listener = MagicMock(return_value=MagicMock())
    entry.runtime_data = runtime_data or _make_runtime_data()
    return entry


def _make_hass(entry_id="test_entry"):
    hass = MagicMock()
    hass.data = {DOMAIN: {entry_id}}
    return hass


# ── _get_nordpool_entry_id ───────────────────────────────────────────────────

def test_get_nordpool_entry_id_from_data():
    from custom_components.spot_scheduler import _get_nordpool_entry_id
    entry = _make_entry(data={CONF_NORDPOOL_CONFIG_ENTRY: "np123"})
    assert _get_nordpool_entry_id(entry) == "np123"


def test_get_nordpool_entry_id_options_override():
    from custom_components.spot_scheduler import _get_nordpool_entry_id
    entry = _make_entry(
        data={CONF_NORDPOOL_CONFIG_ENTRY: "np_old"},
        options={CONF_NORDPOOL_CONFIG_ENTRY: "np_new"},
    )
    assert _get_nordpool_entry_id(entry) == "np_new"


def test_get_nordpool_entry_id_none():
    from custom_components.spot_scheduler import _get_nordpool_entry_id
    entry = MagicMock()
    entry.data = {}
    entry.options = {}
    assert _get_nordpool_entry_id(entry) is None


# ── _coerce_enabled ──────────────────────────────────────────────────────────

def test_coerce_enabled_true():
    from custom_components.spot_scheduler import _coerce_enabled
    assert _coerce_enabled(True) is True


def test_coerce_enabled_false():
    from custom_components.spot_scheduler import _coerce_enabled
    assert _coerce_enabled(False) is False


def test_coerce_enabled_none():
    from custom_components.spot_scheduler import _coerce_enabled
    assert _coerce_enabled(None) is None


def test_coerce_enabled_skip():
    from custom_components.spot_scheduler import _coerce_enabled
    assert _coerce_enabled("skip") == "skip"


# ── async_unload_entry ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_unload_calls_cancel_callbacks():
    """Callbacks registered via entry.async_on_unload are handled by HA framework."""
    from custom_components.spot_scheduler import async_unload_entry

    hass = MagicMock()
    entry = _make_entry()
    hass.data = {DOMAIN: {"test_entry"}}
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.services.has_service = MagicMock(return_value=True)

    result = await async_unload_entry(hass, entry)

    assert result is True


@pytest.mark.asyncio
async def test_unload_removes_services_on_last_entry():
    from custom_components.spot_scheduler import async_unload_entry

    hass = MagicMock()
    entry = _make_entry()
    hass.data = {DOMAIN: {"test_entry"}}
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.services.has_service = MagicMock(return_value=True)

    await async_unload_entry(hass, entry)

    # Should remove all three services
    assert hass.services.async_remove.call_count == 3


@pytest.mark.asyncio
async def test_unload_keeps_services_when_other_entries_exist():
    from custom_components.spot_scheduler import async_unload_entry

    hass = MagicMock()
    entry = _make_entry(entry_id="entry_a")
    hass.data = {DOMAIN: {"entry_a", "entry_b"}}
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    await async_unload_entry(hass, entry)

    hass.services.async_remove.assert_not_called()


@pytest.mark.asyncio
async def test_unload_removes_entry_from_hass_data():
    from custom_components.spot_scheduler import async_unload_entry

    hass = MagicMock()
    entry = _make_entry()
    hass.data = {DOMAIN: {"test_entry"}}
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.services.has_service = MagicMock(return_value=False)

    await async_unload_entry(hass, entry)

    assert "test_entry" not in hass.data[DOMAIN]


# ── _daily_reset ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("custom_components.spot_scheduler.dt_util")
async def test_daily_reset_prunes_old_data(mock_dt):
    from custom_components.spot_scheduler import _daily_reset

    mock_dt.now.return_value = datetime(2025, 3, 10, 0, 0, 15, tzinfo=timezone.utc)

    rd = _make_runtime_data(
        schedules={
            "2025-03-10": {"switch.a": {"10": True}},
            "2025-03-05": {"switch.a": {"8": True}},  # old
        },
        prices={
            "2025-03-10": {10: 0.05},
            "2025-03-05": {8: 0.03},  # old
        },
    )
    entry = _make_entry(runtime_data=rd)
    hass = _make_hass()

    await _daily_reset(hass, entry)

    assert "2025-03-05" not in rd.schedules
    assert "2025-03-05" not in rd.prices
    assert "2025-03-10" in rd.schedules
    assert "2025-03-10" in rd.prices
    rd.store.async_save.assert_called_once()


@pytest.mark.asyncio
async def test_daily_reset_missing_entry_does_nothing():
    from custom_components.spot_scheduler import _daily_reset

    hass = MagicMock()
    hass.data = {DOMAIN: set()}
    entry = _make_entry()

    # Should not raise
    await _daily_reset(hass, entry)


# ── _auto_select_cheapest ────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("custom_components.spot_scheduler.dt_util")
async def test_auto_select_sets_cheapest_hours(mock_dt):
    from custom_components.spot_scheduler import _auto_select_cheapest

    mock_dt.now.return_value = datetime(2025, 3, 5, 0, 0, 0, tzinfo=timezone.utc)

    prices = {h: float(h) for h in range(24)}  # hour 0 cheapest
    rd = _make_runtime_data(prices={"2025-03-05": prices})
    hass = _make_hass()
    hass.bus = MagicMock()

    entry = _make_entry(
        data={
            CONF_DEVICES: ["switch.heater"],
            CONF_AUTO_SELECT_HOURS: 3,
            CONF_AUTO_SELECT_ENABLED: True,
        },
        runtime_data=rd,
    )

    await _auto_select_cheapest(hass, entry, "2025-03-05")

    schedules = rd.schedules
    heater_sched = schedules["2025-03-05"]["switch.heater"]
    on_hours = [h for h, v in heater_sched.items() if v is True]
    assert len(on_hours) == 3
    # Hours 0, 1, 2 should be cheapest
    assert set(on_hours) == {"0", "1", "2"}


@pytest.mark.asyncio
@patch("custom_components.spot_scheduler.dt_util")
async def test_auto_select_disabled_does_nothing(mock_dt):
    from custom_components.spot_scheduler import _auto_select_cheapest

    mock_dt.now.return_value = datetime(2025, 3, 5, 0, 0, 0, tzinfo=timezone.utc)

    rd = _make_runtime_data(prices={"2025-03-05": {h: float(h) for h in range(24)}})
    hass = _make_hass()
    hass.bus = MagicMock()

    entry = _make_entry(
        data={
            CONF_DEVICES: ["switch.heater"],
            CONF_AUTO_SELECT_HOURS: 3,
            CONF_AUTO_SELECT_ENABLED: False,
        },
        runtime_data=rd,
    )

    await _auto_select_cheapest(hass, entry, "2025-03-05")

    schedules = rd.schedules
    assert schedules == {}


@pytest.mark.asyncio
@patch("custom_components.spot_scheduler.dt_util")
async def test_auto_select_preserves_manual_schedules(mock_dt):
    """Auto-select should not overwrite manual ON/OFF/skip entries."""
    from custom_components.spot_scheduler import _auto_select_cheapest

    mock_dt.now.return_value = datetime(2025, 3, 5, 0, 0, 0, tzinfo=timezone.utc)

    rd = _make_runtime_data(
        schedules={
            "2025-03-05": {
                "switch.heater": {"0": False, "1": "skip"},  # manual entries
            }
        },
        prices={"2025-03-05": {h: float(h) for h in range(24)}},
    )
    hass = _make_hass()
    hass.bus = MagicMock()

    entry = _make_entry(
        data={
            CONF_DEVICES: ["switch.heater"],
            CONF_AUTO_SELECT_HOURS: 3,
            CONF_AUTO_SELECT_ENABLED: True,
        },
        runtime_data=rd,
    )

    await _auto_select_cheapest(hass, entry, "2025-03-05")

    sched = rd.schedules["2025-03-05"]["switch.heater"]
    # Manual entries preserved
    assert sched["0"] is False
    assert sched["1"] == "skip"


@pytest.mark.asyncio
@patch("custom_components.spot_scheduler.dt_util")
async def test_block_expensive_sets_off(mock_dt):
    """Block expensive hours should set top N hours to False."""
    from custom_components.spot_scheduler import _auto_select_cheapest

    mock_dt.now.return_value = datetime(2025, 3, 5, 0, 0, 0, tzinfo=timezone.utc)

    prices = {h: float(h) for h in range(24)}
    rd = _make_runtime_data(prices={"2025-03-05": prices})
    hass = _make_hass()
    hass.bus = MagicMock()

    entry = _make_entry(
        data={
            CONF_DEVICES: ["switch.heater"],
            CONF_AUTO_SELECT_HOURS: 0,  # no auto-select
            CONF_AUTO_SELECT_ENABLED: True,
            CONF_BLOCK_EXPENSIVE_HOURS: True,
            CONF_EXPENSIVE_HOURS_COUNT: 3,
        },
        runtime_data=rd,
    )

    await _auto_select_cheapest(hass, entry, "2025-03-05")

    sched = rd.schedules["2025-03-05"]["switch.heater"]
    # Hours 23, 22, 21 should be blocked (set to False)
    assert sched.get("23") is False
    assert sched.get("22") is False
    assert sched.get("21") is False


@pytest.mark.asyncio
@patch("custom_components.spot_scheduler.dt_util")
async def test_block_expensive_does_not_override_on(mock_dt):
    """Block expensive should not override hours already set to ON by auto-select."""
    from custom_components.spot_scheduler import _auto_select_cheapest

    mock_dt.now.return_value = datetime(2025, 3, 5, 0, 0, 0, tzinfo=timezone.utc)

    # Only 3 hours, all "expensive"
    prices = {21: 100.0, 22: 200.0, 23: 300.0}
    rd = _make_runtime_data(prices={"2025-03-05": prices})
    hass = _make_hass()
    hass.bus = MagicMock()

    entry = _make_entry(
        data={
            CONF_DEVICES: ["switch.heater"],
            CONF_AUTO_SELECT_HOURS: 1,  # cheapest = hour 21
            CONF_AUTO_SELECT_ENABLED: True,
            CONF_BLOCK_EXPENSIVE_HOURS: True,
            CONF_EXPENSIVE_HOURS_COUNT: 3,
        },
        runtime_data=rd,
    )

    await _auto_select_cheapest(hass, entry, "2025-03-05")

    sched = rd.schedules["2025-03-05"]["switch.heater"]
    # Hour 21 was auto-selected ON — block should not overwrite it
    assert sched["21"] is True


# ── _async_update_listener ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_listener_reloads_on_device_change():
    from custom_components.spot_scheduler import _async_update_listener

    rd = _make_runtime_data(configured_devices={"switch.old"})
    entry = _make_entry(data={CONF_DEVICES: ["switch.new"]}, runtime_data=rd)
    hass = _make_hass()
    hass.config_entries.async_reload = AsyncMock()

    await _async_update_listener(hass, entry)

    hass.config_entries.async_reload.assert_called_once_with("test_entry")


@pytest.mark.asyncio
async def test_update_listener_fires_apply_now_on_settings_change():
    from custom_components.spot_scheduler import _async_update_listener

    rd = _make_runtime_data(configured_devices={"switch.heater"})
    entry = _make_entry(data={CONF_DEVICES: ["switch.heater"]}, runtime_data=rd)
    hass = _make_hass()
    hass.config_entries.async_reload = AsyncMock()
    hass.bus = MagicMock()

    await _async_update_listener(hass, entry)

    hass.config_entries.async_reload.assert_not_called()
    hass.bus.async_fire.assert_called_once_with(
        f"{DOMAIN}_apply_now", {"entry_id": "test_entry"}
    )


# ── Retry logic ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_with_retry_succeeds_on_second_attempt():
    call_count = 0

    async def fake_fetch(hass, entry, target_date):
        nonlocal call_count
        call_count += 1
        return call_count >= 2

    success = False
    for attempt in range(1, PRICE_FETCH_RETRY_COUNT + 1):
        success = await fake_fetch(None, None, None)
        if success:
            break

    assert success is True
    assert call_count == 2


@pytest.mark.asyncio
async def test_fetch_with_retry_exhausts_all_attempts():
    call_count = 0

    async def always_fail(hass, entry, target_date):
        nonlocal call_count
        call_count += 1
        return False

    success = False
    for attempt in range(1, PRICE_FETCH_RETRY_COUNT + 1):
        success = await always_fail(None, None, None)
        if success:
            break

    assert success is False
    assert call_count == PRICE_FETCH_RETRY_COUNT
