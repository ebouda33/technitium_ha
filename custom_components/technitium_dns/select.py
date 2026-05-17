"""Select entities for Technitium DNS."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TechnitiumConfigEntry
from .const import CONF_ENABLE_SELECTS, DEFAULT_ENABLE_ENTITIES
from .coordinator import TechnitiumDataUpdateCoordinator

PAUSE_DURATION_OPTIONS = {
    "1 min": 1,
    "5 min": 5,
    "10 min": 10,
    "30 min": 30,
    "60 min": 60,
}


async def async_setup_entry(
    hass,
    entry: TechnitiumConfigEntry,
    async_add_entities,
) -> None:
    """Set up Technitium DNS selects."""
    data = {**entry.data, **entry.options}
    if not data.get(CONF_ENABLE_SELECTS, DEFAULT_ENABLE_ENTITIES):
        return

    async_add_entities(
        [TechnitiumPauseDurationSelect(entry.runtime_data, entry.entry_id)]
    )


class TechnitiumPauseDurationSelect(
    CoordinatorEntity[TechnitiumDataUpdateCoordinator],
    SelectEntity,
):
    """Select the pause duration used by the selected pause button."""

    _attr_has_entity_name = True
    _attr_translation_key = "pause_duration"
    _attr_options = list(PAUSE_DURATION_OPTIONS)

    def __init__(
        self,
        coordinator: TechnitiumDataUpdateCoordinator,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_pause_duration"

    @property
    def current_option(self) -> str:
        """Return the selected pause duration."""
        for label, minutes in PAUSE_DURATION_OPTIONS.items():
            if minutes == self.coordinator.selected_pause_minutes:
                return label
        return "5 min"

    async def async_select_option(self, option: str) -> None:
        """Select a pause duration."""
        self.coordinator.selected_pause_minutes = PAUSE_DURATION_OPTIONS[option]
        self.async_write_ha_state()
