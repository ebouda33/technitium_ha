"""Buttons for Technitium DNS."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TechnitiumConfigEntry
from .coordinator import TechnitiumDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class TechnitiumPauseButtonEntityDescription(ButtonEntityDescription):
    """Describes a Technitium pause button."""

    minutes: int


PAUSE_BUTTONS: tuple[TechnitiumPauseButtonEntityDescription, ...] = (
    TechnitiumPauseButtonEntityDescription(
        key="pause_blocking_1_minute",
        translation_key="pause_blocking_1_minute",
        minutes=1,
    ),
    TechnitiumPauseButtonEntityDescription(
        key="pause_blocking_5_minutes",
        translation_key="pause_blocking_5_minutes",
        minutes=5,
    ),
    TechnitiumPauseButtonEntityDescription(
        key="pause_blocking_10_minutes",
        translation_key="pause_blocking_10_minutes",
        minutes=10,
    ),
)


async def async_setup_entry(
    hass,
    entry: TechnitiumConfigEntry,
    async_add_entities,
) -> None:
    """Set up Technitium DNS buttons."""
    coordinator = entry.runtime_data
    async_add_entities(
        TechnitiumPauseButton(coordinator, entry.entry_id, description)
        for description in PAUSE_BUTTONS
    )


class TechnitiumPauseButton(
    CoordinatorEntity[TechnitiumDataUpdateCoordinator],
    ButtonEntity,
):
    """Button to temporarily suspend Technitium DNS blocking."""

    entity_description: TechnitiumPauseButtonEntityDescription

    def __init__(
        self,
        coordinator: TechnitiumDataUpdateCoordinator,
        entry_id: str,
        description: TechnitiumPauseButtonEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_has_entity_name = True

    async def async_press(self) -> None:
        """Temporarily disable DNS blocking."""
        await self.coordinator.api.async_temporary_disable_blocking(
            self.entity_description.minutes
        )
        await self.coordinator.async_request_refresh()
