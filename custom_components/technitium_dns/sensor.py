"""Sensors for Technitium DNS."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import TechnitiumConfigEntry
from .const import CONF_ENABLE_SENSORS, DEFAULT_ENABLE_ENTITIES
from .coordinator import TechnitiumDataUpdateCoordinator
from .entity import build_device_info


@dataclass(frozen=True, kw_only=True)
class TechnitiumSensorEntityDescription(SensorEntityDescription):
    """Describes a Technitium sensor."""

    value_fn: Callable[[dict[str, Any]], int | str | None]


def _counter(key: str) -> Callable[[dict[str, Any]], int | None]:
    def value(data: dict[str, Any]) -> int | None:
        counters = data.get("metrics", {}).get("lifetimeCounters", {})
        return counters.get(key)

    return value


def _setting(key: str) -> Callable[[dict[str, Any]], Any]:
    def value(data: dict[str, Any]) -> Any:
        return data.get("settings", {}).get(key)

    return value


def _blocklist_count(data: dict[str, Any]) -> int | None:
    blocklists = data.get("settings", {}).get("blockListUrls")
    if isinstance(blocklists, list):
        return len(blocklists)
    if isinstance(blocklists, str):
        return len([url for url in blocklists.split(",") if url.strip()])
    return None


def _blocking_percentage(data: dict[str, Any]) -> float | None:
    counters = data.get("metrics", {}).get("lifetimeCounters", {})
    total = counters.get("totalQueries")
    blocked = counters.get("totalBlocked")
    if not total or blocked is None:
        return None
    return round(blocked / total * 100, 2)


def _find_numeric_key(data: Any, keys: set[str]) -> int | float | None:
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys and isinstance(value, int | float):
                return value
        for value in data.values():
            found = _find_numeric_key(value, keys)
            if found is not None:
                return found
    if isinstance(data, list):
        for item in data:
            found = _find_numeric_key(item, keys)
            if found is not None:
                return found
    return None


def _today_stat(keys: set[str]) -> Callable[[dict[str, Any]], int | float | None]:
    def value(data: dict[str, Any]) -> int | float | None:
        return _find_numeric_key(data.get("day_stats", {}), keys)

    return value


def _blocking_status(data: dict[str, Any]) -> str:
    settings = data.get("settings", {})
    if not settings.get("enableBlocking"):
        return "disabled"
    if _pause_remaining(data):
        return "paused"
    return "active"


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return dt_util.parse_datetime(value)


def _pause_until(data: dict[str, Any]) -> datetime | None:
    value = data.get("temporary_disable_until") or data.get("settings", {}).get(
        "temporaryDisableBlockingTill"
    )
    return _parse_datetime(value)


def _pause_remaining(data: dict[str, Any]) -> int | None:
    paused_until = _pause_until(data)
    if paused_until is None:
        return None
    now = datetime.now(paused_until.tzinfo) if paused_until.tzinfo else datetime.utcnow()
    remaining = int((paused_until - now).total_seconds())
    return max(remaining, 0)


SENSORS: tuple[TechnitiumSensorEntityDescription, ...] = (
    TechnitiumSensorEntityDescription(
        key="blocking_status",
        translation_key="blocking_status",
        value_fn=_blocking_status,
    ),
    TechnitiumSensorEntityDescription(
        key="pause_remaining",
        translation_key="pause_remaining",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=_pause_remaining,
    ),
    TechnitiumSensorEntityDescription(
        key="version",
        translation_key="version",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_setting("version"),
    ),
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
    TechnitiumSensorEntityDescription(
        key="blocking_percentage",
        translation_key="blocking_percentage",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_blocking_percentage,
    ),
    TechnitiumSensorEntityDescription(
        key="queries_today",
        translation_key="queries_today",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_today_stat({"totalQueries", "queries", "queryCount"}),
    ),
    TechnitiumSensorEntityDescription(
        key="blocked_today",
        translation_key="blocked_today",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_today_stat({"totalBlocked", "blocked", "blockedCount"}),
    ),
    TechnitiumSensorEntityDescription(
        key="blocklist_count",
        translation_key="blocklist_count",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_blocklist_count,
    ),
    TechnitiumSensorEntityDescription(
        key="blocklist_next_update",
        translation_key="blocklist_next_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _parse_datetime(
            data.get("settings", {}).get("blockListNextUpdatedOn")
        ),
    ),
)


async def async_setup_entry(
    hass,
    entry: TechnitiumConfigEntry,
    async_add_entities,
) -> None:
    """Set up Technitium DNS sensors."""
    data = {**entry.data, **entry.options}
    if not data.get(CONF_ENABLE_SENSORS, DEFAULT_ENABLE_ENTITIES):
        return

    coordinator = entry.runtime_data
    async_add_entities(
        TechnitiumSensor(coordinator, entry.entry_id, entry.title, description)
        for description in SENSORS
    )


class TechnitiumSensor(CoordinatorEntity[TechnitiumDataUpdateCoordinator], SensorEntity):
    """Technitium DNS sensor."""

    entity_description: TechnitiumSensorEntityDescription

    def __init__(
        self,
        coordinator: TechnitiumDataUpdateCoordinator,
        entry_id: str,
        entry_title: str,
        description: TechnitiumSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_has_entity_name = False
        self._attr_device_info = build_device_info(coordinator, entry_id, entry_title)

    @property
    def native_value(self) -> int | str | None:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)
