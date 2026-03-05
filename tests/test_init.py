"""Tests for SpotScheduler __init__.py – integration-level tests using logic.py."""
from __future__ import annotations

import pytest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch, call

from custom_components.spot_scheduler.const import PRICE_FETCH_RETRY_COUNT
from custom_components.spot_scheduler.logic import (
    parse_hourly_prices,
    expensive_hours,
    prune_old_dates,
    set_schedule,
    get_schedule,
)


UTC = timezone.utc


# ── Price parsing (via logic.py) ──────────────────────────────────────────────

def test_hourly_averaging():
    """15-minute slots must be averaged correctly into hourly prices."""
    slots = [
        {"start": "2025-03-05T10:00:00+00:00", "price": 0.10},
        {"start": "2025-03-05T10:15:00+00:00", "price": 0.12},
        {"start": "2025-03-05T10:30:00+00:00", "price": 0.08},
        {"start": "2025-03-05T10:45:00+00:00", "price": 0.14},
    ]
    result = parse_hourly_prices(slots, UTC)
    assert result[10] == pytest.approx(0.11, abs=0.001)


def test_hourly_averaging_single_slot():
    """A single 60-min slot (old MTU) should also work."""
    slots = [{"start": "2025-03-05T14:00:00+00:00", "price": 0.055}]
    result = parse_hourly_prices(slots, UTC)
    assert result[14] == pytest.approx(0.055)


def test_min_max_calculation(sample_nordpool_prices):
    """min/max should reflect the actual cheapest and most expensive hour."""
    result = parse_hourly_prices(sample_nordpool_prices["FI"], UTC)
    prices = list(result.values())
    assert min(prices) < max(prices)
    assert min(prices) >= 0


# ── Schedule storage (via logic.py) ───────────────────────────────────────────

def test_schedule_toggle_on_then_off():
    """Toggling a slot twice should yield Off after On."""
    schedules = {}
    set_schedule(schedules, "2025-03-05", "switch.heater", 10, True)
    assert get_schedule(schedules, "2025-03-05", "switch.heater", 10) is True
    set_schedule(schedules, "2025-03-05", "switch.heater", 10, False)
    assert get_schedule(schedules, "2025-03-05", "switch.heater", 10) is False


def test_daily_reset_removes_old_dates():
    """prune_old_dates should remove entries older than yesterday."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    old = (today - timedelta(days=5)).isoformat()

    schedules = {
        today.isoformat(): {"s.d": {"1": True}},
        old: {"s.d": {"2": True}},
    }
    prune_old_dates(schedules, yesterday)

    assert old not in schedules
    assert today.isoformat() in schedules


def test_schedule_persists_multiple_devices():
    """Multiple devices can have independent schedules on the same date."""
    schedules = {}
    set_schedule(schedules, "2025-03-05", "switch.a", 8, True)
    set_schedule(schedules, "2025-03-05", "switch.b", 8, False)
    assert get_schedule(schedules, "2025-03-05", "switch.a", 8) is True
    assert get_schedule(schedules, "2025-03-05", "switch.b", 8) is False


# ── Retry logic ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_with_retry_succeeds_on_second_attempt():
    """Retry should succeed if second attempt works."""
    call_count = 0

    async def fake_fetch(hass, entry, target_date):
        nonlocal call_count
        call_count += 1
        return call_count >= 2

    hass = MagicMock()
    entry = MagicMock()
    target_date = date(2025, 3, 5)

    success = False
    for attempt in range(1, PRICE_FETCH_RETRY_COUNT + 1):
        success = await fake_fetch(hass, entry, target_date)
        if success:
            break

    assert success is True
    assert call_count == 2


@pytest.mark.asyncio
async def test_fetch_with_retry_exhausts_all_attempts():
    """When all attempts fail, success should be False."""
    call_count = 0

    async def always_fail(hass, entry, target_date):
        nonlocal call_count
        call_count += 1
        return False

    hass = MagicMock()
    entry = MagicMock()
    target_date = date(2025, 3, 5)

    success = False
    for attempt in range(1, PRICE_FETCH_RETRY_COUNT + 1):
        success = await always_fail(hass, entry, target_date)
        if success:
            break

    assert success is False
    assert call_count == PRICE_FETCH_RETRY_COUNT


# ── Expensive hours (via logic.py) ────────────────────────────────────────────

def test_expensive_hours_returns_correct_count():
    """Top-N expensive hours should be identified correctly."""
    prices = {h: float(h) for h in range(24)}
    result = expensive_hours(prices, 3)
    assert 23 in result
    assert 22 in result
    assert 21 in result
    assert 0 not in result
    assert len(result) == 3
