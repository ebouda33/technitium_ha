# Home Assistant Technitium DNS

Custom integration for Technitium DNS Server.

## Features

- Configure the Technitium URL and API token from the Home Assistant UI.
- Enable or suspend DNS blocking with a switch.
- Temporarily pause DNS blocking for 1, 5, or 10 minutes with buttons.
- Expose dashboard lifetime metrics as diagnostic sensors.

## Install

Copy `custom_components/technitium_dns` into your Home Assistant `custom_components`
directory, then restart Home Assistant.

Add the integration from **Settings > Devices & services > Add integration** and
search for **Technitium DNS**.

## Token

Technitium DNS Server v15+ expects API tokens in the HTTP authorization header:

```text
Authorization: Bearer <token>
```

Create a non-expiring API token from the Technitium web console, preferably for
a dedicated user with only the required permissions:

- Dashboard: View
- Settings: View and Modify

## API endpoints used

- `GET /api/settings/get`
- `POST /api/settings/set` with `enableBlocking=true|false`
- `POST /api/settings/temporaryDisableBlocking` with `minutes=1|5|10`
- `GET /api/dashboard/metrics/json`
