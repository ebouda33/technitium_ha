"""Constants for the Technitium DNS integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "technitium_dns"

CONF_TOKEN = "token"
CONF_TIMEOUT = "timeout"
CONF_VERIFY_SSL = "verify_ssl"
CONF_DEFAULT_PAUSE_MINUTES = "default_pause_minutes"
CONF_ENABLE_BUTTONS = "enable_buttons"
CONF_ENABLE_SELECTS = "enable_selects"
CONF_ENABLE_SENSORS = "enable_sensors"
CONF_ENABLE_SWITCHES = "enable_switches"

DEFAULT_NAME = "Technitium DNS"
DEFAULT_PAUSE_MINUTES = 5
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_TIMEOUT = 10
DEFAULT_VERIFY_SSL = True
DEFAULT_ENABLE_ENTITIES = True
MIN_SCAN_INTERVAL = 15
MIN_TIMEOUT = 1

PLATFORMS = ["button", "select", "sensor", "switch"]

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
