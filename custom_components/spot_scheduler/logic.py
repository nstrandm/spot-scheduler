"""Pure logic functions for SpotScheduler – no Home Assistant dependency."""
from __future__ import annotations

from datetime import datetime, date, timedelta, timezone, tzinfo
from typing import Any


def parse_hourly_prices(
    area_data: list[dict[str, Any]],
    tz: tzinfo | None = None,
) -> dict[int, float]:
    """
    Average 15-min (or 60-min) price slots into hourly buckets.

    Parameters
    ----------
    area_data : list of dicts with "start" (str or datetime) and "price" (numeric).
    tz : target timezone for hour mapping.  If None, uses UTC.

    Returns
    -------
    dict mapping hour (0-23) to averaged price (rounded to 5 decimals).
    """
    if tz is None:
        tz = timezone.utc

    hourly: dict[int, list[float]] = {}
    for slot in area_data:
        start = slot.get("start")
        price = slot.get("price")
        if start is None or price is None:
            continue
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        local_hour = start.astimezone(tz).hour
        # Nord Pool returns EUR/MWh; convert to EUR/kWh
        hourly.setdefault(local_hour, []).append(float(price) / 1000.0)

    return {h: round(sum(v) / len(v), 5) for h, v in hourly.items()}


def expensive_hours(prices: dict[int, float], count: int) -> set[int]:
    """
    Return the `count` most expensive hours from a price dict.

    Parameters
    ----------
    prices : dict mapping hour (0-23) to price.
    count : how many top-priced hours to return.

    Returns
    -------
    set of hour integers.
    """
    if not prices or count <= 0:
        return set()
    sorted_hours = sorted(prices, key=lambda h: prices[h], reverse=True)
    return set(sorted_hours[:count])


def prune_old_dates(
    data: dict[str, Any],
    cutoff_date: date,
) -> list[str]:
    """
    Remove entries with date keys strictly before `cutoff_date`.

    Parameters
    ----------
    data : dict with ISO date string keys.
    cutoff_date : dates before this are removed (exclusive).

    Returns
    -------
    list of removed keys.
    """
    cutoff = cutoff_date.isoformat()
    old_keys = [k for k in data if k < cutoff]
    for k in old_keys:
        del data[k]
    return old_keys


def set_schedule(
    schedules: dict,
    target_date: str,
    device_id: str,
    hour: int,
    enabled: bool,
) -> None:
    """Set a single hour slot in the schedule dict (mutates in place)."""
    (
        schedules
        .setdefault(target_date, {})
        .setdefault(device_id, {})
    )[str(hour)] = enabled


def get_schedule(
    schedules: dict,
    target_date: str,
    device_id: str,
    hour: int,
) -> bool | None:
    """Get the scheduled state for a device/hour, or None if unset."""
    return (
        schedules
        .get(target_date, {})
        .get(device_id, {})
        .get(str(hour))
    )


def count_enabled_slots(schedules: dict, target_date: str) -> int:
    """Count how many slots are enabled (True) for a given date."""
    today_sched = schedules.get(target_date, {})
    return sum(
        sum(1 for v in hours.values() if v)
        for hours in today_sched.values()
    )


def should_poll_tomorrow(
    tomorrow_fetched: bool,
    current_hour: int,
    poll_start_hour: int,
    prices: dict,
    tomorrow_iso: str,
) -> bool:
    """Determine whether we should attempt to fetch tomorrow's prices."""
    if tomorrow_fetched:
        return False
    if current_hour < poll_start_hour:
        return False
    if tomorrow_iso in prices:
        return False
    return True
