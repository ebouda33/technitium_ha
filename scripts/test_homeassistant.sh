#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INTEGRATION_NAME="technitium_dns"
SOURCE_DIR="$ROOT_DIR/custom_components/$INTEGRATION_NAME"

HA_CONFIG_DIR="${HA_CONFIG_DIR:-$ROOT_DIR/.ha-test}"
HA_PORT="${HA_PORT:-8123}"
HA_IMAGE="${HA_IMAGE:-ghcr.io/home-assistant/home-assistant:stable}"
CONTAINER_NAME="${CONTAINER_NAME:-ha-technitium-test}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but was not found in PATH." >&2
  exit 1
fi

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Integration directory not found: $SOURCE_DIR" >&2
  exit 1
fi

mkdir -p "$HA_CONFIG_DIR/custom_components"
rm -rf "$HA_CONFIG_DIR/custom_components/$INTEGRATION_NAME"
cp -R "$SOURCE_DIR" "$HA_CONFIG_DIR/custom_components/$INTEGRATION_NAME"

cat > "$HA_CONFIG_DIR/configuration.yaml" <<'YAML'
# Minimal Home Assistant config for local custom integration testing.
default_config:
YAML

echo "Home Assistant test config: $HA_CONFIG_DIR"
echo "Integration copied to: $HA_CONFIG_DIR/custom_components/$INTEGRATION_NAME"
echo
echo "Starting Home Assistant on http://localhost:$HA_PORT"
echo
echo "When adding the integration, if Technitium runs on this Mac, use:"
echo "  http://host.docker.internal:5380"
echo "instead of localhost."
echo

exec docker run --rm -it \
  --name "$CONTAINER_NAME" \
  -p "$HA_PORT:8123" \
  -v "$HA_CONFIG_DIR:/config" \
  "$HA_IMAGE"
