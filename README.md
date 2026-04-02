# QLD Service Station Prices (Home Assistant custom integration)

This integration is for users in Queensland, Australia and gives you sensors for fuel stations in one or more areas and statistics for your Home Assistant dashboards. It uses the Queensland Government Mandatory Fuel Price Reporting Scheme API.

## Setup

1. Request a Data Consumer Token from this form: [Publisher and Data Consumer Sign Up](https://forms.office.com/Pages/ResponsePage.aspx?id=XbdJc0AKKUSHYhmf2mnq-9XqCWIciN5Osw2Y74gWzu9UQ0pCR1dPV0FWR1ZPN0FYSEc0UEVQMkQzMyQlQCN0PWcu)
2. Install the integration by copying the [`custom_components/qld_servo_price`](custom_components/qld_servo_price) folder into your Home Assistant `config/custom_components/` directory (create `custom_components` if needed), then restart Home Assistant. You can also install from a private Git repository with HACS **Custom repositories** if you publish this repo there.
3. Add the integration under **Settings** -> **Devices & services** -> **Add integration** and search for **QLD Service Station Prices**.

### Migrating from another integration domain

If you previously used a different integration domain (for example after renaming this fork), remove the old integration entry in Home Assistant, delete the old folder under `config/custom_components/`, install this package, and add the integration again. Entity IDs and automations that referenced the old domain must be updated.

### Install/config parameters

| Name | Required | Default | Range | Description |
|---|---|---|---|---|
| `subscriber_token` | Yes (master entry only) | None | N/A | Data Consumer Token from Fuel Prices QLD. |
| `location_entity` | No | None | Entity domain: `person`, `device_tracker`, `sensor` | Optional tracked entity used as the reference coordinates. |
| `zone` | Yes | `zone.home` | Entity domain: `zone` | Fallback location and display name source when `location_entity` is not provided. |
| `radius` | Yes | `5` | `1-100` km | Search radius used to include nearby stations. |
| `fuel_types` | Yes | `["12","5","3"]` | Any subset of supported fuel IDs | Fuel products to create sensors for. |
| `scan_interval` | Yes | `6` | `1-24` hours | Scheduled refresh interval for API updates. |
| `enable_geo_entities` | No | `false` | boolean | When enabled, creates one `geo_location` entity per in-range station and tracked fuel (in addition to price sensors). Use Map card **Geolocation sources** with source `qld_servo_price` once instead of listing each entity. |

## Features
- Automatically creates an entry for each station within a selectable radius from your home's location (will add location selector to allow second instance scanning near work, etc)
- Allows you to select multiple fuel types you want added to home assistant
- Tracks the price for those fuel types (duh)
- Tracks the cheapest price in your defined area
- Tracks the cheapest price in Queensland
- Tracks statistics in attributes (7 & 14 day lows & averages)
- Configurable update interval
- Optional map pins via `geo_location` entities (off by default; see `enable_geo_entities`)

### Map card (optional geolocation)

If you enable **Map geolocation entities** in the integration options or initial setup:

- Home Assistant creates roughly one `geo_location.*` entity per station and fuel type you track within the radius (the entity registry can grow quickly when many stations are in range).
- On a Map card, add **Geolocation sources** and set the source to `qld_servo_price` so all those pins appear without adding each entity under **Entities**.
- Pin state is distance (km) from your configured reference point; fuel and price appear in the entity name and in attributes (for example `label_mode: attribute` with `price` if you configure the card that way).

### Price statistics

Station and best-price sensors use `state_class: measurement` with unit `c/L`. Home Assistant records **long-term statistics** as **min, max, and mean** over time, which matches a spot price that goes up and down. They are **not** cumulative meters: `total` / `total_increasing` and sum-style statistics are for consumptions such as energy or water, not for interpreting a sequence of price readings.

### Reviewer note: device class and units on fuel price sensors

This integration intentionally leaves **`device_class` unset** (`None`) for station and best-price sensors and uses the native unit **`c/L`** (cents per liter), aligned with how Queensland fuel prices are quoted and with the upstream API.

**Why not `SensorDeviceClass.MONETARY`?** In Home Assistant, **monetary** sensors represent an **amount in a currency** (for example a balance or a single total in `AUD`). A pump price is a **rate**: money **per liter**. Using `MONETARY` with `AUD` would suggest the state is “this many dollars” in the ordinary sense, while the entity is really “this many cents **per liter**.” That mismatch would be misleading for semantics, statistics consumers, and anyone relying on device-class assumptions.

**Why not energy “cost” patterns?** The Energy dashboard and typical **cost** entities are built around **measured consumption** (for example electricity in kWh) and **tariffs** (for example `$/kWh`). This integration exposes **retail spot prices** from the mandatory reporting API, not a home’s energy meter or a utility tariff entity, so those cost models do not apply directly.

The **last API response** diagnostic sensor uses `SensorDeviceClass.TIMESTAMP` where that meaning is exact. For price entities, **`measurement` + `c/L` + no device class** is the deliberate, accurate choice.

## Development quality gates
- Tests: `python -m pytest -q tests/components/qld_servo_price`
- Coverage: configured in CI with `--cov-fail-under=95`
- Strict typing: `python -m mypy --config-file mypy.ini custom_components/qld_servo_price`

![3 fuel sensors on a dashboard](previews/preview2.png "3 fuel sensors with graphs on a dashboard")

Each sensor has the following attributes:
- Difference (in cents) to cheapest in QLD
- Difference (in cents) to cheapest in your defined area
- 7 day low price
- Difference between 7 day low and current
- 7 day average
- 14 day low price
- Difference between 14 day low and current
- 14 day average
- Distance (in case you want to do a price delta vs distance graph)

![Preview of a sensor with its attributes](previews/preview1.jpg "Preview of sensor panel")



## Note
The scheme is documented here: [Fuel Prices Queensland](https://fuelpricesqld.com.au/)
The API is documented here: [API documentation](https://www.fuelpricesqld.com.au/documents/FuelPricesQLDDirectAPI(OUT)v1.6.pdf)
Sorry about the washed out screenshots, HDR on Hyprland is not yet perfect.

### To do
Add a location selector to the configuration page to allow second instance in a different location
Get non-washed out screenshots with longer term statistics

## Service action: refresh_prices

The integration exposes one Home Assistant service action:

- `qld_servo_price.refresh_prices`

Use this when you want an on-demand update (for example after changing options,
or when troubleshooting stale values).

Expected behavior:

- Triggers a refresh request for all loaded QLD Service Station Prices config entries.
- If shared API data is older than 5 minutes, the integration fetches fresh data.
- If shared API data was fetched in the last 5 minutes, entries reuse the shared
  cache and recompute from that data.

Failure behavior:

- If one or more entries fail during the service call, Home Assistant reports the
  service call as failed (translated error message). Refreshes for other entries
  still run first; failed entry IDs are listed in the message.
- Entry-level failures are logged; successful entries can still update before the
  call raises.

When the API rejects the subscriber token during a scheduled or manual refresh,
the integration opens a reauthentication flow for that config entry (in addition
to the Repairs issue) so you can supply a new token.

## Examples

Manual refresh from an automation:

```yaml
automation:
  - alias: Refresh fuel prices before a trip
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - action: qld_servo_price.refresh_prices
```

Map card (optional geolocation entities enabled): add **Geolocation sources** and
set source to `qld_servo_price` so pins from this integration appear without listing each
`geo_location.*` entity under **Entities**.

## Removal instructions

1. Go to **Settings -> Devices & Services** in Home Assistant.
2. Open **QLD Service Station Prices**.
3. Select the config entry you want to remove.
4. Use **Delete** (three-dot menu) and confirm.
5. Optionally remove dashboards and automations that referenced those entities.

## Troubleshooting

- **Invalid token**: confirm your Data Consumer Token is current, copied exactly,
  and has no leading or trailing spaces.
- **Cannot connect**: check Home Assistant internet connectivity and retry later.
  Temporary upstream API issues can also cause this.
- **Missing zone/location coordinates**: ensure your selected `zone` or
  `location_entity` exposes valid `latitude` and `longitude` attributes.
  If no valid coordinates are available, nearby station filtering cannot be
  calculated correctly.

## Data update behavior

- `scan_interval` controls scheduled refresh frequency in hours (default `6`,
  supported range `1-24`).
- All entries share one cached raw API payload at the integration domain level.
- Shared cache freshness window is 5 minutes. Within that window, refreshes reuse
  cached API data to avoid extra upstream calls.
- After the 5-minute window expires, the next refresh fetches fresh data and
  updates the shared cache for all entries.

## Supported functions

This integration currently supports:

- Setup via Home Assistant config flow.
- Per-location fuel station sensors for selected fuel types.
- Best-price summary sensors (local, nearby tracker location, tracked areas, and
  Queensland-wide).
- Reconfiguration of location, radius, fuel types, and scan interval.
- Reauthentication when a token is no longer accepted by the API.
- Diagnostics snapshots with sensitive values redacted.
- Manual refresh via the `qld_servo_price.refresh_prices` action.

## Supported devices and entities

This integration creates Home Assistant service-style devices and sensor entities:

- A service device for each configured location entry.
- A statewide service device for Queensland-level summary sensors.
- Per-station fuel price sensors for stations in range.
- Optional `geo_location` map pins (same data as sensors; off by default).
- Summary sensors for:
  - best local price for each selected fuel type
  - best nearby price for each selected fuel type
  - best tracked-areas price for each selected fuel type (master entry)
  - best Queensland price for each selected fuel type (master entry)

## Use cases

Common ways to use this integration:

- Compare local stations and pick the best price before refueling.
- Track fuel trends using 7-day and 14-day price attributes.
- Monitor a second area (for example near work) with another config entry.
- Drive automations and dashboard cards from cheapest-price sensors.
- Trigger an immediate refresh before trips with `qld_servo_price.refresh_prices`.

## Known limitations

- Fuel price data quality and update timing depend on the upstream Queensland Fuel
  Prices API.
- If your selected `zone` or `location_entity` has no valid coordinates, nearby
  station filtering and local comparisons cannot be calculated correctly.
- Shared API payloads are cached for up to 5 minutes across entries; immediate
  back-to-back refresh requests may reuse cached data.
- A specific location source can only be configured once (duplicate location setup
  is blocked by unique entry handling).

## Discovery applicability

The Home Assistant Integration Quality Scale rules `discovery` and
`discovery-update-info` are not applicable for this integration.

Reason:

- `qld_servo_price` is a cloud polling service integration that requires a user-provided
  Fuel Prices QLD Data Consumer Token.
- Entities are scoped to user-selected location context (`zone` and optional
  `location_entity`), radius, and chosen fuel products.
- There is no local network device, protocol broadcast, or hardware endpoint to
  discover automatically.
- Setup is intentionally manual through the config flow so users only install and
  configure the integration when it is relevant to their interests and location.

## Attribution

This integration builds on ideas and code from the public Queensland fuel price
Home Assistant integration. See [NOTICE](NOTICE) for the upstream reference and
fork relationship.

Maintainers: set `documentation` and `issue_tracker` in
[`custom_components/qld_servo_price/manifest.json`](custom_components/qld_servo_price/manifest.json)
to your GitHub repository URL (placeholders may remain until you publish).
