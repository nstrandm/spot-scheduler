"""Config flow for SpotScheduler."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector, EntitySelectorConfig,
    NumberSelector, NumberSelectorConfig, NumberSelectorMode,
    SelectSelector, SelectSelectorConfig, SelectSelectorMode, SelectOptionDict,
    TextSelector, TextSelectorConfig, TextSelectorType,
)

from .const import (
    DOMAIN,
    NORDPOOL_DOMAIN,
    CONF_NORDPOOL_CONFIG_ENTRY,
    CONF_DEVICES,
    CONF_EXPENSIVE_HOURS_COUNT,
    DEFAULT_EXPENSIVE_HOURS,
)


def _nordpool_entries(hass):
    return hass.config_entries.async_entries(NORDPOOL_DOMAIN)



class SpotSchedulerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Two-step config flow. Multiple instances allowed (one per Nord Pool area)."""

    VERSION = 1

    def __init__(self) -> None:
        self._step1: dict = {}

    async def async_step_user(self, user_input=None):
        """Step 1 – choose Nord Pool entry, name, expensive-hours slider."""
        entries = _nordpool_entries(self.hass)

        if not entries:
            return self.async_abort(reason="nordpool_not_found")

        if user_input is not None:
            if "expensive_hours_count" in user_input:
                user_input["expensive_hours_count"] = int(user_input["expensive_hours_count"])
            self._step1 = user_input
            return await self.async_step_devices()

        options = [
            SelectOptionDict(value=e.entry_id, label=e.title) for e in entries
        ]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name", default="SpotScheduler"): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
                vol.Required(CONF_NORDPOOL_CONFIG_ENTRY, default=entries[0].entry_id): SelectSelector(
                    SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST)
                ),
                vol.Optional(CONF_EXPENSIVE_HOURS_COUNT, default=DEFAULT_EXPENSIVE_HOURS): NumberSelector(
                    NumberSelectorConfig(min=0, max=12, step=1, mode=NumberSelectorMode.SLIDER)
                ),
            }),
        )

    async def async_step_devices(self, user_input=None):
        """Step 2 – pick devices from entity list."""
        errors: dict[str, str] = {}

        if user_input is not None:
            devices = user_input.get(CONF_DEVICES, [])
            if not devices:
                errors[CONF_DEVICES] = "no_devices_selected"
            else:
                return self.async_create_entry(
                    title=self._step1.get("name", "SpotScheduler"),
                    data={**self._step1, CONF_DEVICES: devices},
                )

        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICES): EntitySelector(
                    EntitySelectorConfig(
                        domain=["switch", "light", "climate", "input_boolean"],
                        multiple=True,
                    )
                ),
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SpotSchedulerOptionsFlow()


class SpotSchedulerOptionsFlow(config_entries.OptionsFlow):
    """Options flow – Nord Pool integration and device list only.

    Other settings (price thresholds, expensive hours, per-device auto-select)
    are exposed as EntityCategory.CONFIG number entities on the device info page.
    """

    async def async_step_init(self, user_input=None):
        merged = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            # Only store the fields from this form + preserve existing options
            # (number entity writes etc.) – avoid duplicating entry.data keys.
            new_opts = {**self.config_entry.options, **user_input}
            return self.async_create_entry(title="", data=new_opts)

        np_entries = _nordpool_entries(self.hass)
        np_options = [
            SelectOptionDict(value=e.entry_id, label=e.title) for e in np_entries
        ]
        devices: list[str] = merged.get(CONF_DEVICES, [])

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_NORDPOOL_CONFIG_ENTRY,
                    default=merged.get(CONF_NORDPOOL_CONFIG_ENTRY,
                                       np_entries[0].entry_id if np_entries else ""),
                ): SelectSelector(
                    SelectSelectorConfig(options=np_options, mode=SelectSelectorMode.LIST)
                ),
                vol.Required(CONF_DEVICES, default=devices): EntitySelector(
                    EntitySelectorConfig(
                        domain=["switch", "light", "climate", "input_boolean"],
                        multiple=True,
                    )
                ),
            }),
        )
