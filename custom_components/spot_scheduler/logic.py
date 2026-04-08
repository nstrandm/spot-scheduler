"""Pure logic functions for SpotScheduler – no Home Assistant dependency."""

from datetime import datetime, date, timedelta, timezone, tzinfo
from typing import Any


def parse_hourly_prices(
    area_data: list[dict[str, Any]],
    tz: tzinfo | None = None,
) -> dict[str, dict[int, float]]:
    """
    Average 15-min (or 60-min) price slots into hourly buckets, keyed by local date.

    Parameters
    ----------
    area_data : list of dicts with "start" (str or datetime) and "price" (numeric).
    tz : target timezone for date/hour mapping.  If None, uses UTC.

    Returns
    -------
    dict mapping local-date ISO string → {hour (0-23): averaged price (EUR/kWh)}.

    Nord Pool returns CET-calendar-day data.  For UTC+ timezones the early local
    morning hours (e.g. Finnish 00:00–00:45 at UTC+2) belong to the *previous*
    CET day's response.  By bucketing per local *date* the caller can merge two
    consecutive Nord Pool responses to build a complete 24-hour picture.
    """
    if tz is None:
        tz = timezone.utc

    # hourly[local_date][local_hour] = list of EUR/kWh values
    hourly: dict[str, dict[int, list[float]]] = {}
    for slot in area_data:
        start = slot.get("start")
        price = slot.get("price")
        if start is None or price is None:
            continue
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        local_dt = start.astimezone(tz)
        local_date = local_dt.date().isoformat()
        local_hour = local_dt.hour
        # Nord Pool returns EUR/MWh; convert to EUR/kWh
        hourly.setdefault(local_date, {}).setdefault(local_hour, []).append(
            float(price) / 1000.0
        )

    return {
        d: {h: round(sum(v) / len(v), 5) for h, v in hours.items()}
        for d, hours in hourly.items()
    }


def cheapest_hours(prices: dict[int, float], count: int) -> set[int]:
    """
    Return the `count` cheapest hours from a price dict.

    Parameters
    ----------
    prices : dict mapping hour (0-23) to price.
    count : how many lowest-priced hours to return.

    Returns
    -------
    set of hour integers.
    """
    if not prices or count <= 0:
        return set()
    sorted_hours = sorted(prices, key=lambda h: prices[h])
    return set(sorted_hours[:count])


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
    enabled: bool | None | str,
) -> None:
    """Set a single hour slot in the schedule dict (mutates in place).

    Pass enabled=None to clear the slot (use default).
    Pass enabled="skip" for explicit don't touch (overrides default_state).
    """
    if enabled is None:
        schedules.get(target_date, {}).get(device_id, {}).pop(str(hour), None)
    else:
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
) -> bool | str | None:
    """Get the scheduled state for a device/hour, or None if unset.

    Returns True (on), False (off), "skip" (explicit don't touch), or None (use default).
    """
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
        sum(1 for v in hours.values() if v is True)
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
