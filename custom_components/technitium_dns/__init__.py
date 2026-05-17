"""Home Assistant integration for Technitium DNS."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TechnitiumApiClient
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    DEFAULT_SCAN_INTERVAL,
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
    api = TechnitiumApiClient(session, data[CONF_URL], data[CONF_TOKEN])
    update_interval = timedelta(
        seconds=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    coordinator = TechnitiumDataUpdateCoordinator(hass, api, update_interval)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: TechnitiumConfigEntry,
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
