"""Buttons for Technitium DNS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TechnitiumConfigEntry
from .const import CONF_ENABLE_BUTTONS, DEFAULT_ENABLE_ENTITIES
from .coordinator import TechnitiumDataUpdateCoordinator
from .entity import build_device_info


@dataclass(frozen=True, kw_only=True)
class TechnitiumPauseButtonEntityDescription(ButtonEntityDescription):
    """Describes a Technitium pause button."""

    action_fn: Callable[[TechnitiumDataUpdateCoordinator], Awaitable[None]]


async def _pause_for(
    coordinator: TechnitiumDataUpdateCoordinator,
    minutes: int,
) -> None:
    """Pause blocking for a fixed duration."""
    await coordinator.api.async_temporary_disable_blocking(minutes)


async def _pause_selected(coordinator: TechnitiumDataUpdateCoordinator) -> None:
    """Pause blocking for the selected duration."""
    await coordinator.api.async_temporary_disable_blocking(
        coordinator.selected_pause_minutes
    )


async def _reactivate(coordinator: TechnitiumDataUpdateCoordinator) -> None:
    """Reactivate blocking now."""
    await coordinator.api.async_set_blocking(True)


async def _flush_cache(coordinator: TechnitiumDataUpdateCoordinator) -> None:
    """Flush DNS cache."""
    await coordinator.api.async_flush_cache()


async def _force_update_blocklists(
    coordinator: TechnitiumDataUpdateCoordinator,
) -> None:
    """Force block lists update."""
    await coordinator.api.async_force_update_blocklists()


PAUSE_BUTTONS: tuple[TechnitiumPauseButtonEntityDescription, ...] = (
    TechnitiumPauseButtonEntityDescription(
        key="pause_blocking_1_minute",
        translation_key="pause_blocking_1_minute",
        action_fn=lambda coordinator: _pause_for(coordinator, 1),
    ),
    TechnitiumPauseButtonEntityDescription(
        key="pause_blocking_5_minutes",
        translation_key="pause_blocking_5_minutes",
        action_fn=lambda coordinator: _pause_for(coordinator, 5),
    ),
    TechnitiumPauseButtonEntityDescription(
        key="pause_blocking_10_minutes",
        translation_key="pause_blocking_10_minutes",
        action_fn=lambda coordinator: _pause_for(coordinator, 10),
    ),
    TechnitiumPauseButtonEntityDescription(
        key="pause_blocking_30_minutes",
        translation_key="pause_blocking_30_minutes",
        action_fn=lambda coordinator: _pause_for(coordinator, 30),
    ),
    TechnitiumPauseButtonEntityDescription(
        key="pause_blocking_60_minutes",
        translation_key="pause_blocking_60_minutes",
        action_fn=lambda coordinator: _pause_for(coordinator, 60),
    ),
    TechnitiumPauseButtonEntityDescription(
        key="pause_blocking_selected",
        translation_key="pause_blocking_selected",
        action_fn=_pause_selected,
    ),
    TechnitiumPauseButtonEntityDescription(
        key="reactivate_blocking",
        translation_key="reactivate_blocking",
        action_fn=_reactivate,
    ),
    TechnitiumPauseButtonEntityDescription(
        key="flush_cache",
        translation_key="flush_cache",
        action_fn=_flush_cache,
    ),
    TechnitiumPauseButtonEntityDescription(
        key="force_update_blocklists",
        translation_key="force_update_blocklists",
        action_fn=_force_update_blocklists,
    ),
)


async def async_setup_entry(
    hass,
    entry: TechnitiumConfigEntry,
    async_add_entities,
) -> None:
    """Set up Technitium DNS buttons."""
    data = {**entry.data, **entry.options}
    if not data.get(CONF_ENABLE_BUTTONS, DEFAULT_ENABLE_ENTITIES):
        return

    coordinator = entry.runtime_data
    async_add_entities(
        TechnitiumPauseButton(coordinator, entry.entry_id, entry.title, description)
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
        entry_title: str,
        description: TechnitiumPauseButtonEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_device_info = build_device_info(coordinator, entry_id, entry_title)

    async def async_press(self) -> None:
        """Run the Technitium DNS action."""
        await self.entity_description.action_fn(self.coordinator)
        await self.coordinator.async_request_refresh()
