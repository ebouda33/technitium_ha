"""Home Assistant integration for Technitium DNS."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TechnitiumApiClient
from .const import (
    CONF_DEFAULT_PAUSE_MINUTES,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    CONF_TOKEN,
    CONF_VERIFY_SSL,
    DEFAULT_PAUSE_MINUTES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import TechnitiumDataUpdateCoordinator

TechnitiumConfigEntry = ConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TechnitiumConfigEntry,
) -> bool:
    """Set up Technitium DNS from a config entry."""
    session = async_get_clientsession(hass)
    data = {**entry.data, **entry.options}
    api = TechnitiumApiClient(
        session,
        data[CONF_URL],
        data[CONF_TOKEN],
        timeout=data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        verify_ssl=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
    )
    update_interval = timedelta(
        seconds=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    coordinator = TechnitiumDataUpdateCoordinator(hass, api, update_interval)
    coordinator.selected_pause_minutes = data.get(
        CONF_DEFAULT_PAUSE_MINUTES, DEFAULT_PAUSE_MINUTES
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: TechnitiumConfigEntry,
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(
    hass: HomeAssistant,
    entry: TechnitiumConfigEntry,
) -> None:
    """Reload Technitium DNS when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
