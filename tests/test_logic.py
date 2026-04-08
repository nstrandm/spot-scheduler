"""Tests for SpotScheduler logic.py – pure functions, no HA dependency."""

import pytest
from datetime import date, datetime, timedelta, timezone, tzinfo

from custom_components.spot_scheduler.logic import (
    parse_hourly_prices,
    expensive_hours,
    cheapest_hours,
    prune_old_dates,
    set_schedule,
    get_schedule,
    count_enabled_slots,
    should_poll_tomorrow,
)


# ── Timezone helpers for deterministic tests ──────────────────────────────────

UTC = timezone.utc
HELSINKI = timezone(timedelta(hours=2))  # EET (simplified, no DST)

# parse_hourly_prices returns {date_str: {hour: price_eur_kwh}}
# and divides input prices by 1000 (EUR/MWh → EUR/kWh).
# Helper to extract the single-date result:

def _single_date(result: dict) -> dict[int, float]:
    """Extract the first (only) date's hour→price dict from parse result."""
    assert len(result) == 1, f"Expected single date, got {list(result.keys())}"
    return next(iter(result.values()))


# ── parse_hourly_prices ───────────────────────────────────────────────────────

def test_15min_slots_averaged_correctly():
    """Four 15-min slots in the same hour should be averaged."""
    slots = [
        {"start": "2025-03-05T10:00:00+00:00", "price": 100},
        {"start": "2025-03-05T10:15:00+00:00", "price": 120},
        {"start": "2025-03-05T10:30:00+00:00", "price": 80},
        {"start": "2025-03-05T10:45:00+00:00", "price": 140},
    ]
    result = _single_date(parse_hourly_prices(slots, UTC))
    # (100+120+80+140)/4 = 110 EUR/MWh = 0.11 EUR/kWh
    assert result[10] == pytest.approx(0.11, abs=0.001)


def test_single_60min_slot_passthrough():
    """A single slot should pass through (divided by 1000)."""
    slots = [{"start": "2025-03-05T14:00:00+00:00", "price": 55}]
    result = _single_date(parse_hourly_prices(slots, UTC))
    assert result[14] == pytest.approx(0.055)


def test_timezone_mapping():
    """UTC 10:00 should map to hour 12 in Helsinki (UTC+2)."""
    slots = [{"start": "2025-03-05T10:00:00+00:00", "price": 50}]
    result = _single_date(parse_hourly_prices(slots, HELSINKI))
    assert 12 in result
    assert 10 not in result


def test_default_timezone_is_utc():
    """When no timezone given, should default to UTC."""
    slots = [{"start": "2025-03-05T10:00:00+00:00", "price": 50}]
    result = _single_date(parse_hourly_prices(slots))
    assert 10 in result


def test_skips_slots_with_missing_fields():
    """Slots missing start or price should be silently skipped."""
    slots = [
        {"start": "2025-03-05T10:00:00+00:00", "price": 50},
        {"start": "2025-03-05T11:00:00+00:00"},           # no price
        {"price": 60},                                      # no start
        {},                                                  # empty
    ]
    result = _single_date(parse_hourly_prices(slots, UTC))
    assert len(result) == 1
    assert result[10] == pytest.approx(0.05)


def test_empty_input_returns_empty():
    result = parse_hourly_prices([], UTC)
    assert result == {}


def test_negative_prices():
    """Negative prices (possible on Nord Pool) should be handled."""
    slots = [
        {"start": "2025-03-05T03:00:00+00:00", "price": -10},
        {"start": "2025-03-05T03:15:00+00:00", "price": -30},
    ]
    result = _single_date(parse_hourly_prices(slots, UTC))
    # (-10 + -30) / 2 = -20 EUR/MWh = -0.02 EUR/kWh
    assert result[3] == pytest.approx(-0.02, abs=0.001)


def test_full_day_24_hours():
    """96 slots (15-min for 24 hours) should produce 24 hourly entries."""
    slots = []
    for hour in range(24):
        for minute in [0, 15, 30, 45]:
            slots.append({
                "start": f"2025-03-05T{hour:02d}:{minute:02d}:00+00:00",
                "price": 50 + hour * 3,  # EUR/MWh
            })
    result = _single_date(parse_hourly_prices(slots, UTC))
    assert len(result) == 24
    # Hour 0: 50/1000=0.05, Hour 23: (50+23*3)/1000=0.119
    assert min(result.values()) == pytest.approx(0.05)
    assert max(result.values()) == pytest.approx((50 + 23 * 3) / 1000)


def test_multi_date_result():
    """Slots spanning midnight in a target timezone produce two dates."""
    # UTC 22:00 on Mar 5 = Mar 6 00:00 in Helsinki (UTC+2)
    slots = [
        {"start": "2025-03-05T10:00:00+00:00", "price": 50},
        {"start": "2025-03-05T22:00:00+00:00", "price": 60},
    ]
    result = parse_hourly_prices(slots, HELSINKI)
    # First slot: Helsinki 12:00 on 2025-03-05
    # Second slot: Helsinki 00:00 on 2025-03-06
    assert "2025-03-05" in result
    assert 12 in result["2025-03-05"]
    assert "2025-03-06" in result
    assert 0 in result["2025-03-06"]


# ── expensive_hours ───────────────────────────────────────────────────────────

def test_expensive_hours_top_3():
    prices = {h: float(h) for h in range(24)}
    result = expensive_hours(prices, 3)
    assert result == {23, 22, 21}


def test_expensive_hours_top_1():
    prices = {0: 0.10, 1: 0.05, 2: 0.20}
    result = expensive_hours(prices, 1)
    assert result == {2}


def test_expensive_hours_empty_prices():
    assert expensive_hours({}, 3) == set()


def test_expensive_hours_zero_count():
    prices = {0: 0.10, 1: 0.05}
    assert expensive_hours(prices, 0) == set()


def test_expensive_hours_count_exceeds_available():
    prices = {0: 0.10, 1: 0.05}
    result = expensive_hours(prices, 10)
    assert result == {0, 1}


# ── cheapest_hours ───────────────────────────────────────────────────────────

def test_cheapest_hours_top_3():
    prices = {h: float(h) for h in range(24)}
    result = cheapest_hours(prices, 3)
    assert result == {0, 1, 2}


def test_cheapest_hours_empty():
    assert cheapest_hours({}, 3) == set()


def test_cheapest_hours_zero_count():
    assert cheapest_hours({0: 0.1}, 0) == set()


# ── prune_old_dates ───────────────────────────────────────────────────────────

def test_prune_removes_old_keeps_recent():
    today = date.today()
    yesterday = today - timedelta(days=1)
    old = (today - timedelta(days=5)).isoformat()
    data = {
        today.isoformat(): {"some": "data"},
        yesterday.isoformat(): {"yesterday": "data"},
        old: {"old": "data"},
    }
    removed = prune_old_dates(data, yesterday)
    assert old in removed
    assert today.isoformat() in data
    assert yesterday.isoformat() in data
    assert old not in data


def test_prune_empty_dict():
    data = {}
    removed = prune_old_dates(data, date.today())
    assert removed == []


# ── set_schedule / get_schedule ───────────────────────────────────────────────

def test_set_and_get_schedule():
    schedules = {}
    set_schedule(schedules, "2025-03-05", "switch.heater", 10, True)
    assert get_schedule(schedules, "2025-03-05", "switch.heater", 10) is True


def test_toggle_on_then_off():
    schedules = {}
    set_schedule(schedules, "2025-03-05", "switch.heater", 10, True)
    assert get_schedule(schedules, "2025-03-05", "switch.heater", 10) is True
    set_schedule(schedules, "2025-03-05", "switch.heater", 10, False)
    assert get_schedule(schedules, "2025-03-05", "switch.heater", 10) is False


def test_get_schedule_unset_returns_none():
    schedules = {}
    assert get_schedule(schedules, "2025-03-05", "switch.heater", 10) is None


def test_multiple_devices_independent():
    schedules = {}
    set_schedule(schedules, "2025-03-05", "switch.a", 8, True)
    set_schedule(schedules, "2025-03-05", "switch.b", 8, False)
    assert get_schedule(schedules, "2025-03-05", "switch.a", 8) is True
    assert get_schedule(schedules, "2025-03-05", "switch.b", 8) is False


def test_set_schedule_none_clears_slot():
    schedules = {}
    set_schedule(schedules, "2025-03-05", "switch.a", 8, True)
    assert get_schedule(schedules, "2025-03-05", "switch.a", 8) is True
    set_schedule(schedules, "2025-03-05", "switch.a", 8, None)
    assert get_schedule(schedules, "2025-03-05", "switch.a", 8) is None


def test_set_schedule_skip():
    schedules = {}
    set_schedule(schedules, "2025-03-05", "switch.a", 8, "skip")
    assert get_schedule(schedules, "2025-03-05", "switch.a", 8) == "skip"


# ── count_enabled_slots ───────────────────────────────────────────────────────

def test_count_enabled_slots():
    schedules = {}
    set_schedule(schedules, "2025-03-05", "switch.a", 8, True)
    set_schedule(schedules, "2025-03-05", "switch.a", 9, True)
    set_schedule(schedules, "2025-03-05", "switch.a", 10, False)
    set_schedule(schedules, "2025-03-05", "switch.b", 8, True)
    assert count_enabled_slots(schedules, "2025-03-05") == 3


def test_count_enabled_slots_empty():
    assert count_enabled_slots({}, "2025-03-05") == 0


def test_count_ignores_skip():
    schedules = {}
    set_schedule(schedules, "2025-03-05", "switch.a", 8, True)
    set_schedule(schedules, "2025-03-05", "switch.a", 9, "skip")
    assert count_enabled_slots(schedules, "2025-03-05") == 1


# ── should_poll_tomorrow ──────────────────────────────────────────────────────

def test_should_poll_when_not_fetched():
    assert should_poll_tomorrow(
        tomorrow_fetched=False, current_hour=14, poll_start_hour=13,
        prices={}, tomorrow_iso="2025-03-06",
    ) is True


def test_should_not_poll_when_already_fetched():
    assert should_poll_tomorrow(
        tomorrow_fetched=True, current_hour=14, poll_start_hour=13,
        prices={}, tomorrow_iso="2025-03-06",
    ) is False


def test_should_not_poll_before_start_hour():
    assert should_poll_tomorrow(
        tomorrow_fetched=False, current_hour=10, poll_start_hour=13,
        prices={}, tomorrow_iso="2025-03-06",
    ) is False


def test_should_not_poll_when_prices_already_present():
    assert should_poll_tomorrow(
        tomorrow_fetched=False, current_hour=14, poll_start_hour=13,
        prices={"2025-03-06": {0: 0.05}}, tomorrow_iso="2025-03-06",
    ) is False


def test_should_poll_at_boundary_hour():
    """At exactly poll_start_hour should poll."""
    assert should_poll_tomorrow(
        tomorrow_fetched=False, current_hour=13, poll_start_hour=13,
        prices={}, tomorrow_iso="2025-03-06",
    ) is True


# ── Service unload logic (pure) ──────────────────────────────────────────────

def test_services_removed_only_when_last_instance_unloads():
    loaded_entries = {"entry_a", "entry_b"}

    def should_remove(unloading):
        return len([e for e in loaded_entries if e != unloading]) == 0

    assert should_remove("entry_a") is False
    assert should_remove("entry_b") is False

    loaded_entries = {"entry_a"}
    assert should_remove("entry_a") is True
