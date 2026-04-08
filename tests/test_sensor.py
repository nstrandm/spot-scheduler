"""Tests for SpotScheduler sensor platform."""

import asyncio
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date

from custom_components.spot_scheduler import SpotSchedulerData
from custom_components.spot_scheduler.const import (
    DOMAIN,
    CONF_DEFAULT_STATE,
    DEFAULT_DEFAULT_STATE,
)


def _make_runtime_data(**overrides) -> SpotSchedulerData:
    defaults = dict(
        store=MagicMock(),
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


def _make_hass_and_entry(entry_id="test_entry", data=None, options=None, runtime_data=None):
    """Create mock hass and config entry for sensor tests."""
    hass = MagicMock()
    entry = MagicMock()
    entry.entry_id = entry_id
    entry.data = data or {"name": "TestScheduler", "devices": ["switch.heater"]}
    entry.options = options or {}
    entry.runtime_data = runtime_data or _make_runtime_data()

    hass.data = {DOMAIN: {entry_id}}
    return hass, entry


# ── SpotScheduleStatusSensor ────────────────────────────────────────────────

class TestSpotScheduleStatusSensor:

    def _make_sensor(self, hass, entry):
        from custom_components.spot_scheduler.sensor import SpotScheduleStatusSensor
        sensor = SpotScheduleStatusSensor(entry)
        sensor.hass = hass
        return sensor

    def test_native_value_counts_devices(self):
        hass, entry = _make_hass_and_entry(
            data={"name": "Test", "devices": ["switch.a", "switch.b", "switch.c"]},
        )
        sensor = self._make_sensor(hass, entry)
        assert sensor.native_value == 3

    def test_native_value_no_devices(self):
        hass, entry = _make_hass_and_entry(
            data={"name": "Test", "devices": []},
        )
        sensor = self._make_sensor(hass, entry)
        assert sensor.native_value == 0

    def test_native_value_options_override_data(self):
        hass, entry = _make_hass_and_entry(
            data={"name": "Test", "devices": ["switch.a"]},
            options={"devices": ["switch.a", "switch.b"]},
        )
        sensor = self._make_sensor(hass, entry)
        assert sensor.native_value == 2

    @patch("custom_components.spot_scheduler.sensor.dt_util")
    def test_extra_state_attributes_structure(self, mock_dt):
        mock_dt.now.return_value.date.return_value = date(2025, 3, 5)
        rd = _make_runtime_data(
            schedules={"2025-03-05": {"switch.heater": {"10": True}}},
            prices={"2025-03-05": {h: 0.05 + h * 0.001 for h in range(24)}},
            min_price=0.05,
            max_price=0.073,
            tomorrow_fetched=True,
        )
        hass, entry = _make_hass_and_entry(
            data={"name": "Test", "expensive_hours_count": 5, "devices": ["switch.heater"]},
            runtime_data=rd,
        )
        sensor = self._make_sensor(hass, entry)
        attrs = sensor.extra_state_attributes

        assert "schedules" in attrs
        assert "prices" in attrs
        assert "prices_all" in attrs
        assert "schedules_all" in attrs
        assert attrs["min_price"] == 0.05
        assert attrs["max_price"] == 0.073
        assert attrs["tomorrow_fetched"] is True
        assert attrs["expensive_hours_count"] == 5
        assert attrs["devices"] == ["switch.heater"]

    @patch("custom_components.spot_scheduler.sensor.dt_util")
    def test_extra_state_attributes_options_override_data(self, mock_dt):
        """Options should take precedence over data for merged settings."""
        mock_dt.now.return_value.date.return_value = date(2025, 3, 5)
        hass, entry = _make_hass_and_entry(
            data={"name": "Test", "expensive_hours_count": 3, "devices": ["switch.a"]},
            options={"expensive_hours_count": 7, "devices": ["switch.a", "switch.b"]},
        )
        sensor = self._make_sensor(hass, entry)
        attrs = sensor.extra_state_attributes

        assert attrs["expensive_hours_count"] == 7
        assert attrs["devices"] == ["switch.a", "switch.b"]

    @patch("custom_components.spot_scheduler.sensor.dt_util")
    def test_prices_all_filters_incomplete_dates(self, mock_dt):
        """Dates with fewer than 20 hours should be excluded from prices_all."""
        mock_dt.now.return_value.date.return_value = date(2025, 3, 5)
        rd = _make_runtime_data(
            prices={
                "2025-03-05": {h: 0.05 for h in range(24)},  # complete
                "2025-03-06": {0: 0.05, 1: 0.06},             # incomplete
            },
        )
        hass, entry = _make_hass_and_entry(
            data={"name": "Test"},
            runtime_data=rd,
        )
        sensor = self._make_sensor(hass, entry)
        attrs = sensor.extra_state_attributes

        assert "2025-03-05" in attrs["prices_all"]
        assert "2025-03-06" not in attrs["prices_all"]

    @patch("custom_components.spot_scheduler.sensor.dt_util")
    def test_default_state_attribute(self, mock_dt):
        mock_dt.now.return_value.date.return_value = date(2025, 3, 5)
        hass, entry = _make_hass_and_entry(
            options={CONF_DEFAULT_STATE: "on"},
        )
        sensor = self._make_sensor(hass, entry)
        assert sensor.extra_state_attributes["default_state"] == "on"

    @patch("custom_components.spot_scheduler.sensor.dt_util")
    def test_default_state_defaults_to_dont_touch(self, mock_dt):
        mock_dt.now.return_value.date.return_value = date(2025, 3, 5)
        hass, entry = _make_hass_and_entry()
        sensor = self._make_sensor(hass, entry)
        assert sensor.extra_state_attributes["default_state"] == DEFAULT_DEFAULT_STATE

    def test_unique_id(self):
        hass, entry = _make_hass_and_entry(entry_id="abc123")
        sensor = self._make_sensor(hass, entry)
        assert sensor.unique_id == "abc123_managed_devices"

    def test_device_info(self):
        hass, entry = _make_hass_and_entry()
        sensor = self._make_sensor(hass, entry)
        info = sensor.device_info
        assert (DOMAIN, "test_entry") in info["identifiers"]
        assert info["name"] == "TestScheduler"

    def test_should_poll_is_false(self):
        hass, entry = _make_hass_and_entry()
        sensor = self._make_sensor(hass, entry)
        assert sensor.should_poll is False

    def test_data_returns_empty_when_entry_missing(self):
        """If entry data is gone from hass.data, sensor should not crash."""
        hass, entry = _make_hass_and_entry()
        hass.data = {}  # simulate unloaded
        sensor = self._make_sensor(hass, entry)
        # native_value reads from entry config, not hass.data
        assert sensor.native_value == 1  # default fixture has 1 device
