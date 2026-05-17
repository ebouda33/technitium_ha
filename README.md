# Home Assistant Technitium DNS

Custom integration for Technitium DNS Server.

## Features

- Configure the Technitium URL and API token from the Home Assistant UI.
- Configure API timeout, SSL certificate verification, default pause duration,
  and which entity families to create.
- Enable or suspend DNS blocking with a switch.
- Temporarily pause DNS blocking for 1, 5, 10, 30, or 60 minutes with buttons.
- Pick a pause duration from a select entity and trigger it with a button.
- Reactivate blocking, flush DNS cache, and force block list updates with buttons.
- Expose dashboard lifetime metrics as diagnostic sensors.
- Expose blocking status, pause remaining time, version, blocking percentage,
  today's stats when available, and block list update details.

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
- Cache: Delete
- Settings: View and Modify

## API endpoints used

- `GET /api/settings/get`
- `POST /api/settings/set` with `enableBlocking=true|false`
- `POST /api/settings/temporaryDisableBlocking` with `minutes=1|5|10|30|60`
- `POST /api/settings/forceUpdateBlockLists`
- `POST /api/cache/flush`
- `GET /api/dashboard/metrics/json`
- `GET /api/dashboard/stats/get`
