"""Tests for SpotScheduler switch platform."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, datetime, timezone

from custom_components.spot_scheduler import SpotSchedulerData
from custom_components.spot_scheduler.const import (
    DOMAIN,
    CONF_AUTO_SELECT_ENABLED,
    DEFAULT_AUTO_SELECT_ENABLED,
    CONF_BLOCK_EXPENSIVE_HOURS,
    DEFAULT_BLOCK_EXPENSIVE,
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


def _make_entry(entry_id="test_entry", data=None, options=None, runtime_data=None):
    entry = MagicMock()
    entry.entry_id = entry_id
    entry.data = data or {"name": "TestScheduler", "devices": ["switch.heater"]}
    entry.options = options or {}
    entry.runtime_data = runtime_data or _make_runtime_data()
    return entry


# ── SpotAutoSelectSwitch ─────────────────────────────────────────────────────

class TestSpotAutoSelectSwitch:
    def _make(self, entry=None):
        from custom_components.spot_scheduler.switch import SpotAutoSelectSwitch
        return SpotAutoSelectSwitch(entry or _make_entry())

    def test_unique_id(self):
        sw = self._make(_make_entry(entry_id="abc"))
        assert sw.unique_id == "abc_auto_select_enabled"

    def test_is_on_default(self):
        sw = self._make()
        assert sw.is_on is DEFAULT_AUTO_SELECT_ENABLED

    def test_is_on_from_options(self):
        sw = self._make(_make_entry(options={CONF_AUTO_SELECT_ENABLED: False}))
        assert sw.is_on is False

    def test_is_on_options_override_data(self):
        sw = self._make(_make_entry(
            data={CONF_AUTO_SELECT_ENABLED: True},
            options={CONF_AUTO_SELECT_ENABLED: False},
        ))
        assert sw.is_on is False

    @pytest.mark.asyncio
    async def test_turn_on(self):
        entry = _make_entry(options={"some_other": 42})
        sw = self._make(entry)
        sw.hass = MagicMock()
        sw.async_write_ha_state = MagicMock()

        await sw.async_turn_on()
        sw.hass.config_entries.async_update_entry.assert_called_once()
        call_kwargs = sw.hass.config_entries.async_update_entry.call_args
        new_opts = call_kwargs[1]["options"] if "options" in call_kwargs[1] else call_kwargs[0][1]
        assert new_opts[CONF_AUTO_SELECT_ENABLED] is True
        assert new_opts["some_other"] == 42

    @pytest.mark.asyncio
    async def test_turn_off(self):
        entry = _make_entry()
        sw = self._make(entry)
        sw.hass = MagicMock()
        sw.async_write_ha_state = MagicMock()

        await sw.async_turn_off()
        call_kwargs = sw.hass.config_entries.async_update_entry.call_args
        new_opts = call_kwargs[1]["options"] if "options" in call_kwargs[1] else call_kwargs[0][1]
        assert new_opts[CONF_AUTO_SELECT_ENABLED] is False

    def test_device_info(self):
        sw = self._make(_make_entry(data={"name": "MyScheduler"}))
        info = sw.device_info
        assert (DOMAIN, "test_entry") in info["identifiers"]
        assert info["name"] == "MyScheduler"

    def test_should_poll_is_false(self):
        sw = self._make()
        assert sw.should_poll is False


# ── SpotBlockExpensiveSwitch ─────────────────────────────────────────────────

class TestSpotBlockExpensiveSwitch:
    def _make(self, entry=None):
        from custom_components.spot_scheduler.switch import SpotBlockExpensiveSwitch
        return SpotBlockExpensiveSwitch(entry or _make_entry())

    def test_unique_id(self):
        sw = self._make(_make_entry(entry_id="xyz"))
        assert sw.unique_id == "xyz_block_expensive_hours"

    def test_is_on_default(self):
        sw = self._make()
        assert sw.is_on is DEFAULT_BLOCK_EXPENSIVE

    def test_is_on_from_options(self):
        sw = self._make(_make_entry(options={CONF_BLOCK_EXPENSIVE_HOURS: True}))
        assert sw.is_on is True

    @pytest.mark.asyncio
    async def test_turn_on(self):
        entry = _make_entry()
        sw = self._make(entry)
        sw.hass = MagicMock()
        sw.async_write_ha_state = MagicMock()

        await sw.async_turn_on()
        call_kwargs = sw.hass.config_entries.async_update_entry.call_args
        new_opts = call_kwargs[1]["options"] if "options" in call_kwargs[1] else call_kwargs[0][1]
        assert new_opts[CONF_BLOCK_EXPENSIVE_HOURS] is True

    @pytest.mark.asyncio
    async def test_turn_off(self):
        entry = _make_entry()
        sw = self._make(entry)
        sw.hass = MagicMock()
        sw.async_write_ha_state = MagicMock()

        await sw.async_turn_off()
        call_kwargs = sw.hass.config_entries.async_update_entry.call_args
        new_opts = call_kwargs[1]["options"] if "options" in call_kwargs[1] else call_kwargs[0][1]
        assert new_opts[CONF_BLOCK_EXPENSIVE_HOURS] is False


# ── _apply_schedules ─────────────────────────────────────────────────────────

class TestApplySchedules:
    """Test the _apply_schedules function logic."""

    @pytest.mark.asyncio
    @patch("custom_components.spot_scheduler.switch.dt_util")
    async def test_apply_turns_on_scheduled_device(self, mock_dt):
        from custom_components.spot_scheduler.switch import _apply_schedules

        mock_dt.now.return_value = datetime(2025, 3, 5, 10, 0, 5, tzinfo=timezone.utc)
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        hass.data = {DOMAIN: {"test_entry"}}

        rd = _make_runtime_data(
            schedules={"2025-03-05": {"switch.heater": {"10": True}}},
        )
        entry = _make_entry(runtime_data=rd)

        await _apply_schedules(hass, entry, ["switch.heater"])

        hass.services.async_call.assert_called_once_with(
            "switch", "turn_on", {}, blocking=False,
            target={"entity_id": "switch.heater"},
        )

    @pytest.mark.asyncio
    @patch("custom_components.spot_scheduler.switch.dt_util")
    async def test_apply_turns_off_scheduled_device(self, mock_dt):
        from custom_components.spot_scheduler.switch import _apply_schedules

        mock_dt.now.return_value = datetime(2025, 3, 5, 10, 0, 5, tzinfo=timezone.utc)
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        hass.data = {DOMAIN: {"test_entry"}}

        rd = _make_runtime_data(
            schedules={"2025-03-05": {"switch.heater": {"10": False}}},
        )
        entry = _make_entry(runtime_data=rd)

        await _apply_schedules(hass, entry, ["switch.heater"])

        hass.services.async_call.assert_called_once_with(
            "switch", "turn_off", {}, blocking=False,
            target={"entity_id": "switch.heater"},
        )

    @pytest.mark.asyncio
    @patch("custom_components.spot_scheduler.switch.dt_util")
    async def test_apply_skip_leaves_device_alone(self, mock_dt):
        from custom_components.spot_scheduler.switch import _apply_schedules

        mock_dt.now.return_value = datetime(2025, 3, 5, 10, 0, 5, tzinfo=timezone.utc)
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        hass.data = {DOMAIN: {"test_entry"}}

        rd = _make_runtime_data(
            schedules={"2025-03-05": {"switch.heater": {"10": "skip"}}},
        )
        entry = _make_entry(runtime_data=rd)

        await _apply_schedules(hass, entry, ["switch.heater"])
        hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    @patch("custom_components.spot_scheduler.switch.dt_util")
    async def test_apply_default_state_on(self, mock_dt):
        """When no schedule and default_state='on', should turn on."""
        from custom_components.spot_scheduler.switch import _apply_schedules

        mock_dt.now.return_value = datetime(2025, 3, 5, 10, 0, 5, tzinfo=timezone.utc)
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        hass.data = {DOMAIN: {"test_entry"}}

        entry = _make_entry(options={CONF_DEFAULT_STATE: "on"})

        await _apply_schedules(hass, entry, ["switch.heater"])

        hass.services.async_call.assert_called_once_with(
            "switch", "turn_on", {}, blocking=False,
            target={"entity_id": "switch.heater"},
        )

    @pytest.mark.asyncio
    @patch("custom_components.spot_scheduler.switch.dt_util")
    async def test_apply_default_state_off(self, mock_dt):
        from custom_components.spot_scheduler.switch import _apply_schedules

        mock_dt.now.return_value = datetime(2025, 3, 5, 10, 0, 5, tzinfo=timezone.utc)
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        hass.data = {DOMAIN: {"test_entry"}}

        entry = _make_entry(options={CONF_DEFAULT_STATE: "off"})

        await _apply_schedules(hass, entry, ["switch.heater"])

        hass.services.async_call.assert_called_once_with(
            "switch", "turn_off", {}, blocking=False,
            target={"entity_id": "switch.heater"},
        )

    @pytest.mark.asyncio
    @patch("custom_components.spot_scheduler.switch.dt_util")
    async def test_apply_default_state_dont_touch(self, mock_dt):
        """Default 'dont_touch' should not call any service."""
        from custom_components.spot_scheduler.switch import _apply_schedules

        mock_dt.now.return_value = datetime(2025, 3, 5, 10, 0, 5, tzinfo=timezone.utc)
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        hass.data = {DOMAIN: {"test_entry"}}

        entry = _make_entry(options={CONF_DEFAULT_STATE: "dont_touch"})

        await _apply_schedules(hass, entry, ["switch.heater"])
        hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    @patch("custom_components.spot_scheduler.switch.dt_util")
    async def test_apply_missing_entry_data_skips(self, mock_dt):
        """If entry not in hass.data, should silently return."""
        from custom_components.spot_scheduler.switch import _apply_schedules

        mock_dt.now.return_value = datetime(2025, 3, 5, 10, 0, 5, tzinfo=timezone.utc)
        hass = MagicMock()
        hass.data = {DOMAIN: set()}
        entry = _make_entry()

        await _apply_schedules(hass, entry, ["switch.heater"])
        # No exception raised

    @pytest.mark.asyncio
    @patch("custom_components.spot_scheduler.switch.dt_util")
    async def test_apply_multiple_devices(self, mock_dt):
        from custom_components.spot_scheduler.switch import _apply_schedules

        mock_dt.now.return_value = datetime(2025, 3, 5, 14, 0, 5, tzinfo=timezone.utc)
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        hass.data = {DOMAIN: {"test_entry"}}

        rd = _make_runtime_data(
            schedules={"2025-03-05": {
                "switch.heater": {"14": True},
                "switch.pump": {"14": False},
            }},
        )
        entry = _make_entry(runtime_data=rd)

        await _apply_schedules(hass, entry, ["switch.heater", "switch.pump"])

        assert hass.services.async_call.call_count == 2


# ── _apply_schedule_for_device ───────────────────────────────────────────────

class TestApplyScheduleForDevice:

    @pytest.mark.asyncio
    async def test_immediate_turn_on(self):
        from custom_components.spot_scheduler.switch import _apply_schedule_for_device

        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        hass.data = {DOMAIN: {"test_entry"}}
        entry = _make_entry()

        await _apply_schedule_for_device(hass, entry, "switch.heater", True)

        hass.services.async_call.assert_called_once_with(
            "switch", "turn_on", {}, blocking=False,
            target={"entity_id": "switch.heater"},
        )

    @pytest.mark.asyncio
    async def test_immediate_turn_off(self):
        from custom_components.spot_scheduler.switch import _apply_schedule_for_device

        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        hass.data = {DOMAIN: {"test_entry"}}
        entry = _make_entry()

        await _apply_schedule_for_device(hass, entry, "switch.heater", False)

        hass.services.async_call.assert_called_once_with(
            "switch", "turn_off", {}, blocking=False,
            target={"entity_id": "switch.heater"},
        )

    @pytest.mark.asyncio
    async def test_immediate_none_skips(self):
        from custom_components.spot_scheduler.switch import _apply_schedule_for_device

        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        hass.data = {DOMAIN: {"test_entry"}}
        entry = _make_entry()

        await _apply_schedule_for_device(hass, entry, "switch.heater", None)
        hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_immediate_skip_string_skips(self):
        from custom_components.spot_scheduler.switch import _apply_schedule_for_device

        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        hass.data = {DOMAIN: {"test_entry"}}
        entry = _make_entry()

        await _apply_schedule_for_device(hass, entry, "switch.heater", "skip")
        hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_device_id_returns_early(self):
        from custom_components.spot_scheduler.switch import _apply_schedule_for_device

        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        entry = _make_entry()

        await _apply_schedule_for_device(hass, entry, None, True)
        hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_entry_returns_early(self):
        from custom_components.spot_scheduler.switch import _apply_schedule_for_device

        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        hass.data = {DOMAIN: set()}
        entry = _make_entry()

        await _apply_schedule_for_device(hass, entry, "switch.heater", True)
        hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_light_domain_device(self):
        """Device IDs like light.foo should call light.turn_on."""
        from custom_components.spot_scheduler.switch import _apply_schedule_for_device

        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        hass.data = {DOMAIN: {"test_entry"}}
        entry = _make_entry()

        await _apply_schedule_for_device(hass, entry, "light.living_room", True)

        hass.services.async_call.assert_called_once_with(
            "light", "turn_on", {}, blocking=False,
            target={"entity_id": "light.living_room"},
        )
