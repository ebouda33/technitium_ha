"""Constants for the Technitium DNS integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "technitium_dns"

CONF_TOKEN = "token"

DEFAULT_NAME = "Technitium DNS"
DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 15

PLATFORMS = ["button", "sensor", "switch"]

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
