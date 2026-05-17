"""Shared entity helpers for Technitium DNS."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .coordinator import TechnitiumDataUpdateCoordinator


def build_device_info(
    coordinator: TechnitiumDataUpdateCoordinator,
    entry_id: str,
    entry_title: str,
) -> DeviceInfo:
    """Return the shared device information for all Technitium DNS entities."""
    settings: dict[str, Any] = coordinator.data.get("settings", {})
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        manufacturer="Technitium",
        model="DNS Server",
        name=entry_title,
        sw_version=settings.get("version"),
    )
