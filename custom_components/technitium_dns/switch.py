"""Switches for Technitium DNS."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TechnitiumConfigEntry
from .coordinator import TechnitiumDataUpdateCoordinator


async def async_setup_entry(
    hass,
    entry: TechnitiumConfigEntry,
    async_add_entities,
) -> None:
    """Set up Technitium DNS switches."""
    async_add_entities([TechnitiumBlockingSwitch(entry.runtime_data, entry.entry_id)])


class TechnitiumBlockingSwitch(
    CoordinatorEntity[TechnitiumDataUpdateCoordinator],
    SwitchEntity,
):
    """Switch to enable or suspend Technitium DNS blocking."""

    _attr_has_entity_name = True
    _attr_translation_key = "blocking"

    def __init__(
        self,
        coordinator: TechnitiumDataUpdateCoordinator,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_blocking"

    @property
    def is_on(self) -> bool:
        """Return true when DNS blocking is enabled."""
        return bool(self.coordinator.data.get("settings", {}).get("enableBlocking"))

    async def async_turn_on(self, **kwargs) -> None:
        """Enable DNS blocking."""
        await self.coordinator.api.async_set_blocking(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Suspend DNS blocking."""
        await self.coordinator.api.async_set_blocking(False)
        await self.coordinator.async_request_refresh()
