"""Shared pytest fixtures – no HA import here so pure logic tests work standalone."""
from __future__ import annotations
import pytest


@pytest.fixture
def sample_nordpool_prices():
    """Realistic Nord Pool 15-min slot list for one area."""
    slots = []
    for hour in range(24):
        for minute in [0, 15, 30, 45]:
            slots.append({
                "start": f"2025-03-05T{hour:02d}:{minute:02d}:00+00:00",
                "end": f"2025-03-05T{hour:02d}:{minute+14 if minute < 45 else 59}:00+00:00",
                "price": 0.05 + hour * 0.003,
            })
    return {"FI": slots}
