"""Technitium DNS HTTP API client."""

from __future__ import annotations

from json import JSONDecodeError
from typing import Any
from urllib.parse import urljoin

from aiohttp import ClientError, ClientResponseError, ClientSession


class TechnitiumApiError(Exception):
    """Base Technitium API error."""


class TechnitiumCannotConnect(TechnitiumApiError):
    """Raised when Technitium cannot be reached."""


class TechnitiumAuthenticationError(TechnitiumApiError):
    """Raised when the API token is rejected."""


class TechnitiumResponseError(TechnitiumApiError):
    """Raised when Technitium returns an API error."""


class TechnitiumApiClient:
    """Small async client for the Technitium DNS HTTP API."""

    def __init__(self, session: ClientSession, base_url: str, token: str) -> None:
        self._session = session
        self._base_url = self._normalize_url(base_url)
        self._token = token

    @property
    def base_url(self) -> str:
        """Return normalized base URL."""
        return self._base_url

    async def async_get_settings(self) -> dict[str, Any]:
        """Return DNS server settings."""
        data = await self._request("GET", "/api/settings/get")
        return data.get("response", {})

    async def async_set_blocking(self, enabled: bool) -> None:
        """Enable or disable Technitium DNS blocking."""
        await self._request(
            "POST",
            "/api/settings/set",
            data={"enableBlocking": str(enabled).lower()},
        )

    async def async_temporary_disable_blocking(self, minutes: int) -> None:
        """Temporarily disable Technitium DNS blocking."""
        await self._request(
            "POST",
            "/api/settings/temporaryDisableBlocking",
            data={"minutes": str(minutes)},
        )

    async def async_get_metrics(self) -> dict[str, Any]:
        """Return dashboard lifetime metrics."""
        data = await self._request("GET", "/api/dashboard/metrics/json")
        return data.get("response", {})

    async def async_test_connection(self) -> dict[str, Any]:
        """Validate URL and token, returning settings."""
        return await self.async_get_settings()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perform an API request and normalize Technitium errors."""
        url = urljoin(f"{self._base_url}/", path.lstrip("/"))
        headers = {"Authorization": f"Bearer {self._token}"}

        try:
            async with self._session.request(
                method,
                url,
                params=params,
                data=data,
                headers=headers,
            ) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except ClientResponseError as err:
            if err.status in (401, 403):
                raise TechnitiumAuthenticationError from err
            raise TechnitiumCannotConnect from err
        except ClientError as err:
            raise TechnitiumCannotConnect from err
        except JSONDecodeError as err:
            raise TechnitiumCannotConnect from err

        status = payload.get("status")
        if status == "ok":
            return payload

        if status == "invalid-token":
            raise TechnitiumAuthenticationError

        message = payload.get("errorMessage") or "Technitium API error"
        raise TechnitiumResponseError(message)

    @staticmethod
    def _normalize_url(base_url: str) -> str:
        """Normalize the configured server URL."""
        base_url = base_url.strip().rstrip("/")
        if "://" not in base_url:
            base_url = f"http://{base_url}"
        return base_url
