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

## Installation with HACS

This integration can be installed with HACS as a custom repository.

1. Open **HACS** in Home Assistant.
2. Open the three-dot menu in the top right.
3. Select **Custom repositories**.
4. Add this repository URL:

```text
https://github.com/ebouda33/technitium_ha
```

5. Select the category **Integration**.
6. Click **Add**.
7. Search for **Technitium DNS** in HACS.
8. Download the integration.
9. Restart Home Assistant.
10. Open **Settings > Devices & services > Add integration**.
11. Search for **Technitium DNS** and complete the setup.

## Updating with HACS

When a new version is available:

1. Open **HACS**.
2. Open **Technitium DNS**.
3. Click **Update**.
4. Restart Home Assistant.

If HACS reports that a commit version cannot be used, make sure you are using a
published GitHub release such as `v0.1.4`, not only the default branch commit.

## Manual Installation

If you do not use HACS, copy `custom_components/technitium_dns` into your Home
Assistant `custom_components` directory, then restart Home Assistant.

Then add the integration from **Settings > Devices & services > Add integration**
and search for **Technitium DNS**.

## Dashboard

After adding the integration, open your dashboard, choose **Edit dashboard**,
then add a **Manual** card and paste the example from
`examples/dashboard.yaml`.

The default entity IDs are based on the integration name. If you renamed the
integration during setup, replace the `technitium_dns` part in the YAML with
the entity prefix created by Home Assistant.

You can also add entities from the device page:

1. Open **Settings > Devices & services > Technitium DNS**.
2. Open the Technitium DNS device.
3. Use the listed controls and sensors to add the ones you want to a dashboard.

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
