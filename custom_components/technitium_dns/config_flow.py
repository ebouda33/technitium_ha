"""Config flow for Technitium DNS."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    TechnitiumApiClient,
    TechnitiumAuthenticationError,
    TechnitiumCannotConnect,
    TechnitiumResponseError,
)
from .const import (
    CONF_DEFAULT_PAUSE_MINUTES,
    CONF_ENABLE_BUTTONS,
    CONF_ENABLE_SELECTS,
    CONF_ENABLE_SENSORS,
    CONF_ENABLE_SWITCHES,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    CONF_TOKEN,
    CONF_VERIFY_SSL,
    DEFAULT_ENABLE_ENTITIES,
    DEFAULT_NAME,
    DEFAULT_PAUSE_MINUTES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
    MIN_TIMEOUT,
)

PAUSE_MINUTES = [1, 5, 10, 30, 60]


def _user_schema(user_input: dict[str, Any] | None = None) -> vol.Schema:
    user_input = user_input or {}
    return vol.Schema(
        {
            vol.Optional(
                CONF_NAME,
                default=user_input.get(CONF_NAME, DEFAULT_NAME),
            ): str,
            vol.Required(CONF_URL, default=user_input.get(CONF_URL, "")): str,
            vol.Required(CONF_TOKEN, default=user_input.get(CONF_TOKEN, "")): str,
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
            vol.Optional(
                CONF_TIMEOUT,
                default=user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            ): vol.All(vol.Coerce(int), vol.Range(min=MIN_TIMEOUT)),
            vol.Optional(
                CONF_VERIFY_SSL,
                default=user_input.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
            ): bool,
            vol.Optional(
                CONF_DEFAULT_PAUSE_MINUTES,
                default=user_input.get(
                    CONF_DEFAULT_PAUSE_MINUTES, DEFAULT_PAUSE_MINUTES
                ),
            ): vol.In(PAUSE_MINUTES),
            vol.Optional(
                CONF_ENABLE_BUTTONS,
                default=user_input.get(CONF_ENABLE_BUTTONS, DEFAULT_ENABLE_ENTITIES),
            ): bool,
            vol.Optional(
                CONF_ENABLE_SELECTS,
                default=user_input.get(CONF_ENABLE_SELECTS, DEFAULT_ENABLE_ENTITIES),
            ): bool,
            vol.Optional(
                CONF_ENABLE_SENSORS,
                default=user_input.get(CONF_ENABLE_SENSORS, DEFAULT_ENABLE_ENTITIES),
            ): bool,
            vol.Optional(
                CONF_ENABLE_SWITCHES,
                default=user_input.get(CONF_ENABLE_SWITCHES, DEFAULT_ENABLE_ENTITIES),
            ): bool,
        }
    )


async def _validate_input(
    hass: HomeAssistant,
    user_input: dict[str, Any],
) -> dict[str, Any]:
    """Validate user input by querying Technitium."""
    session = async_get_clientsession(hass)
    api = TechnitiumApiClient(
        session,
        user_input[CONF_URL],
        user_input[CONF_TOKEN],
        timeout=user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        verify_ssl=user_input.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
    )
    settings = await api.async_test_connection()
    return {
        "title": user_input.get(CONF_NAME) or settings.get("dnsServerDomain") or DEFAULT_NAME,
        "unique_id": f"{api.base_url}|{settings.get('dnsServerDomain', '')}",
    }


class TechnitiumConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Technitium DNS."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return TechnitiumOptionsFlow(config_entry)

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await _validate_input(self.hass, user_input)
            except TechnitiumAuthenticationError:
                errors["base"] = "invalid_auth"
            except TechnitiumCannotConnect:
                errors["base"] = "cannot_connect"
            except TechnitiumResponseError:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(user_input),
            errors=errors,
        )


class TechnitiumOptionsFlow(config_entries.OptionsFlow):
    """Handle Technitium options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage options."""
        errors: dict[str, str] = {}
        current = {**self._config_entry.data, **self._config_entry.options}

        if user_input is not None:
            try:
                await _validate_input(self.hass, user_input)
            except TechnitiumAuthenticationError:
                errors["base"] = "invalid_auth"
            except TechnitiumCannotConnect:
                errors["base"] = "cannot_connect"
            except TechnitiumResponseError:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_user_schema(current),
            errors=errors,
        )
