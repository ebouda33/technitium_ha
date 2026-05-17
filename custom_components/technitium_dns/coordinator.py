"""Data update coordinator for Technitium DNS."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TechnitiumApiClient, TechnitiumApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TechnitiumDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch Technitium DNS settings and metrics."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: TechnitiumApiClient,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.api = api
        self.selected_pause_minutes = 5

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Technitium."""
        try:
            settings = await self.api.async_get_settings()
            metrics = await self.api.async_get_metrics()
        except TechnitiumApiError as err:
            raise UpdateFailed(str(err)) from err
        try:
            day_stats = await self.api.async_get_stats("LastDay")
        except TechnitiumApiError:
            day_stats = {}

        return {
            "settings": settings,
            "metrics": metrics,
            "day_stats": day_stats,
            "temporary_disable_until": self.api.last_temporary_disable_until,
        }
