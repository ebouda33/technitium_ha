"""Sensors for Technitium DNS."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import UnitOfTime
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TechnitiumConfigEntry
from .coordinator import TechnitiumDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class TechnitiumSensorEntityDescription(SensorEntityDescription):
    """Describes a Technitium sensor."""

    value_fn: Callable[[dict[str, Any]], int | str | None]


def _counter(key: str) -> Callable[[dict[str, Any]], int | None]:
    def value(data: dict[str, Any]) -> int | None:
        counters = data.get("metrics", {}).get("lifetimeCounters", {})
        return counters.get(key)

    return value


SENSORS: tuple[TechnitiumSensorEntityDescription, ...] = (
    TechnitiumSensorEntityDescription(
        key="uptime",
        translation_key="uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("metrics", {}).get("uptimeSeconds"),
    ),
    TechnitiumSensorEntityDescription(
        key="total_queries",
        translation_key="total_queries",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_counter("totalQueries"),
    ),
    TechnitiumSensorEntityDescription(
        key="total_blocked",
        translation_key="total_blocked",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_counter("totalBlocked"),
    ),
    TechnitiumSensorEntityDescription(
        key="total_cached",
        translation_key="total_cached",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_counter("totalCached"),
    ),
    TechnitiumSensorEntityDescription(
        key="total_refused",
        translation_key="total_refused",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_counter("totalRefused"),
    ),
    TechnitiumSensorEntityDescription(
        key="total_clients",
        translation_key="total_clients",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_counter("totalClients"),
    ),
)


async def async_setup_entry(
    hass,
    entry: TechnitiumConfigEntry,
    async_add_entities,
) -> None:
    """Set up Technitium DNS sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        TechnitiumSensor(coordinator, entry.entry_id, description)
        for description in SENSORS
    )


class TechnitiumSensor(CoordinatorEntity[TechnitiumDataUpdateCoordinator], SensorEntity):
    """Technitium DNS sensor."""

    entity_description: TechnitiumSensorEntityDescription

    def __init__(
        self,
        coordinator: TechnitiumDataUpdateCoordinator,
        entry_id: str,
        description: TechnitiumSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_has_entity_name = True

    @property
    def native_value(self) -> int | str | None:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)
