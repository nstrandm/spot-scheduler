"""Tests for SpotScheduler number platform."""

import pytest
from unittest.mock import MagicMock

from custom_components.spot_scheduler.const import (
    DOMAIN,
    CONF_PRICE_THRESHOLD_LOW,
    CONF_PRICE_THRESHOLD_HIGH,
    CONF_AUTO_SELECT_HOURS,
    CONF_EXPENSIVE_HOURS_COUNT,
    DEFAULT_PRICE_THRESHOLD_LOW,
    DEFAULT_PRICE_THRESHOLD_HIGH,
    DEFAULT_AUTO_SELECT_HOURS,
    DEFAULT_EXPENSIVE_HOURS,
)


def _make_entry(entry_id="test_entry", data=None, options=None):
    entry = MagicMock()
    entry.entry_id = entry_id
    entry.data = data or {"name": "TestScheduler"}
    entry.options = options or {}
    return entry


# ── SpotPriceThresholdLowNumber ──────────────────────────────────────────────

class TestSpotPriceThresholdLowNumber:
    def _make(self, entry=None):
        from custom_components.spot_scheduler.number import SpotPriceThresholdLowNumber
        return SpotPriceThresholdLowNumber(entry or _make_entry())

    def test_unique_id(self):
        n = self._make(_make_entry(entry_id="abc"))
        assert n.unique_id == "abc_price_threshold_low"

    def test_default_value(self):
        n = self._make()
        assert n.native_value == DEFAULT_PRICE_THRESHOLD_LOW

    def test_value_from_data(self):
        n = self._make(_make_entry(data={CONF_PRICE_THRESHOLD_LOW: 3.0}))
        assert n.native_value == 3.0

    def test_options_override_data(self):
        n = self._make(_make_entry(
            data={CONF_PRICE_THRESHOLD_LOW: 3.0},
            options={CONF_PRICE_THRESHOLD_LOW: 8.5},
        ))
        assert n.native_value == 8.5

    @pytest.mark.asyncio
    async def test_set_value(self):
        entry = _make_entry()
        n = self._make(entry)
        n.hass = MagicMock()
        n.async_write_ha_state = MagicMock()

        await n.async_set_native_value(7.5)

        n.hass.config_entries.async_update_entry.assert_called_once()
        call_kwargs = n.hass.config_entries.async_update_entry.call_args
        new_opts = call_kwargs[1]["options"] if "options" in call_kwargs[1] else call_kwargs[0][1]
        assert new_opts[CONF_PRICE_THRESHOLD_LOW] == 7.5

    def test_min_max_step(self):
        n = self._make()
        assert n.native_min_value == 0
        assert n.native_max_value == 50
        assert n.native_step == 0.5

    def test_device_info(self):
        n = self._make(_make_entry(data={"name": "MyScheduler"}))
        info = n.device_info
        assert (DOMAIN, "test_entry") in info["identifiers"]


# ── SpotPriceThresholdHighNumber ─────────────────────────────────────────────

class TestSpotPriceThresholdHighNumber:
    def _make(self, entry=None):
        from custom_components.spot_scheduler.number import SpotPriceThresholdHighNumber
        return SpotPriceThresholdHighNumber(entry or _make_entry())

    def test_unique_id(self):
        n = self._make(_make_entry(entry_id="xyz"))
        assert n.unique_id == "xyz_price_threshold_high"

    def test_default_value(self):
        n = self._make()
        assert n.native_value == DEFAULT_PRICE_THRESHOLD_HIGH

    def test_value_from_options(self):
        n = self._make(_make_entry(options={CONF_PRICE_THRESHOLD_HIGH: 20.0}))
        assert n.native_value == 20.0

    @pytest.mark.asyncio
    async def test_set_value(self):
        entry = _make_entry()
        n = self._make(entry)
        n.hass = MagicMock()
        n.async_write_ha_state = MagicMock()

        await n.async_set_native_value(12.0)

        call_kwargs = n.hass.config_entries.async_update_entry.call_args
        new_opts = call_kwargs[1]["options"] if "options" in call_kwargs[1] else call_kwargs[0][1]
        assert new_opts[CONF_PRICE_THRESHOLD_HIGH] == 12.0


# ── SpotAutoSelectHoursNumber ────────────────────────────────────────────────

class TestSpotAutoSelectHoursNumber:
    def _make(self, entry=None):
        from custom_components.spot_scheduler.number import SpotAutoSelectHoursNumber
        return SpotAutoSelectHoursNumber(entry or _make_entry())

    def test_unique_id(self):
        n = self._make(_make_entry(entry_id="e1"))
        assert n.unique_id == "e1_auto_select_hours_global"

    def test_default_value(self):
        n = self._make()
        assert n.native_value == float(DEFAULT_AUTO_SELECT_HOURS)

    def test_value_from_options(self):
        n = self._make(_make_entry(options={CONF_AUTO_SELECT_HOURS: 6}))
        assert n.native_value == 6.0

    def test_legacy_dict_value_falls_back_to_zero(self):
        """Legacy per-device dict should map to 0 (disabled)."""
        n = self._make(_make_entry(data={
            CONF_AUTO_SELECT_HOURS: {"switch.heater": 4, "switch.pump": 2}
        }))
        assert n.native_value == 0.0

    @pytest.mark.asyncio
    async def test_set_value_converts_to_int(self):
        entry = _make_entry()
        n = self._make(entry)
        n.hass = MagicMock()
        n.async_write_ha_state = MagicMock()

        await n.async_set_native_value(5.0)

        call_kwargs = n.hass.config_entries.async_update_entry.call_args
        new_opts = call_kwargs[1]["options"] if "options" in call_kwargs[1] else call_kwargs[0][1]
        assert new_opts[CONF_AUTO_SELECT_HOURS] == 5
        assert isinstance(new_opts[CONF_AUTO_SELECT_HOURS], int)

    def test_min_max_step(self):
        n = self._make()
        assert n.native_min_value == 0
        assert n.native_max_value == 12
        assert n.native_step == 1


# ── SpotExpensiveHoursNumber ─────────────────────────────────────────────────

class TestSpotExpensiveHoursNumber:
    def _make(self, entry=None):
        from custom_components.spot_scheduler.number import SpotExpensiveHoursNumber
        return SpotExpensiveHoursNumber(entry or _make_entry())

    def test_unique_id(self):
        n = self._make(_make_entry(entry_id="e2"))
        assert n.unique_id == "e2_expensive_hours"

    def test_default_value(self):
        n = self._make()
        assert n.native_value == float(DEFAULT_EXPENSIVE_HOURS)

    def test_value_from_options(self):
        n = self._make(_make_entry(options={CONF_EXPENSIVE_HOURS_COUNT: 8}))
        assert n.native_value == 8.0

    @pytest.mark.asyncio
    async def test_set_value_converts_to_int(self):
        entry = _make_entry()
        n = self._make(entry)
        n.hass = MagicMock()
        n.async_write_ha_state = MagicMock()

        await n.async_set_native_value(4.0)

        call_kwargs = n.hass.config_entries.async_update_entry.call_args
        new_opts = call_kwargs[1]["options"] if "options" in call_kwargs[1] else call_kwargs[0][1]
        assert new_opts[CONF_EXPENSIVE_HOURS_COUNT] == 4
        assert isinstance(new_opts[CONF_EXPENSIVE_HOURS_COUNT], int)

    def test_min_max_step(self):
        n = self._make()
        assert n.native_min_value == 0
        assert n.native_max_value == 12
        assert n.native_step == 1
