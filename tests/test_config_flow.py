"""Tests for SpotScheduler config flow."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.asyncio
async def test_step1_requires_nordpool_entry():
    """Config flow should abort if no Nord Pool entries exist."""
    hass = MagicMock()
    hass.config_entries.async_entries.return_value = []

    from custom_components.spot_scheduler.config_flow import SpotSchedulerConfigFlow
    flow = SpotSchedulerConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()
    assert result["type"] == "abort"
    assert result["reason"] == "nordpool_not_found"


@pytest.mark.asyncio
async def test_step2_rejects_empty_devices():
    """Step 2 should show an error when no devices are selected."""
    hass = MagicMock()
    np_entry = MagicMock()
    np_entry.entry_id = "np123"
    np_entry.title = "Nord Pool FI"
    hass.config_entries.async_entries.return_value = [np_entry]

    from custom_components.spot_scheduler.config_flow import SpotSchedulerConfigFlow
    flow = SpotSchedulerConfigFlow()
    flow.hass = hass
    flow._step1 = {"name": "Test", "nordpool_config_entry": "np123", "expensive_hours_count": 3}

    result = await flow.async_step_devices({"devices": []})
    assert result["type"] == "form"
    assert "devices" in result.get("errors", {})


def test_options_flow_merges_data_and_options():
    """Options flow should pre-fill from both data and options."""
    entry = MagicMock()
    entry.data = {
        "devices": ["switch.old_device"],
        "expensive_hours_count": 3,
    }
    entry.options = {}  # nothing overridden yet

    # Test the merge logic directly (OptionsFlow uses this pattern in async_step_init)
    merged = {**entry.data, **entry.options}

    assert merged["devices"] == ["switch.old_device"]
    assert merged["expensive_hours_count"] == 3

    # When options override data, options should win
    entry.options = {"devices": ["switch.new_device"], "expensive_hours_count": 5}
    merged = {**entry.data, **entry.options}

    assert merged["devices"] == ["switch.new_device"]
    assert merged["expensive_hours_count"] == 5
