# QLD Service Station Prices

Home Assistant custom integration for **Queensland (Australia) retail fuel prices** using the Fuel Prices QLD **Mandatory Fuel Price Reporting** data feed (server API).

**Domain:** `qld_servo_price`  
**Integration type:** service (cloud polling)  
**Declared quality scale:** Gold (see `manifest.json` and the [Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/)).

Further reading: [Operations and CI](docs/integration-operations.md) · [API reference (contributors)](docs/fuel-prices-qld-api-reference.md) · [Contributing](CONTRIBUTING.md)

## Requirements

- **Home Assistant** 2024.1 or newer (minimum declared in [`hacs.json`](hacs.json)).
- A valid **Fuel Prices QLD Data Consumer Token** ([publisher and consumer sign-up](https://forms.office.com/Pages/ResponsePage.aspx?id=XbdJc0AKKUSHYhmf2mnq-9XqCWIciN5Osw2Y74gWzu9UQ0pCR1dPV0FWR1ZPN0FYSEc0UEVQMkQzMyQlQCN0PWcu)).
- Outbound HTTPS from Home Assistant to the Fuel Prices QLD API.

## What you get

- **Per-station sensors** for each selected fuel product within your configured radius.
- **Summary sensors** for best prices (nearby, optional statewide and multi-area views).
- **Optional** `geo_location` entities for map pins (off by default).
- **Config flow** for setup, options, reconfigure, and reauthentication when the token fails.
- **Diagnostics** download (sensitive fields redacted).
- **Scheduled polling** plus a manual **refresh** action shared across all entries.

Scheme overview (consumer-facing): [Fuel Prices Queensland](https://fuelpricesqld.com.au/). Official API PDF: [FuelPricesQLDDirectAPI(OUT)v1.6.pdf](https://www.fuelpricesqld.com.au/documents/FuelPricesQLDDirectAPI(OUT)v1.6.pdf).

## Installation

1. Obtain a Data Consumer Token from Fuel Prices QLD (link above).
2. Install the integration:
   - **Manual:** Copy [`custom_components/qld_servo_price`](custom_components/qld_servo_price) into `<config>/custom_components/` on your Home Assistant host, then restart Home Assistant.
   - **HACS:** Add this repository under **HACS > Custom repositories** (if you distribute it that way), then install the integration and restart as prompted.
3. In Home Assistant go to **Settings** > **Devices & services** > **Add integration** and search for **QLD Service Station Prices**.

### Migrating from another custom integration or domain

If you previously used a different domain or fork name: remove the old integration entry, delete the old files under `custom_components/`, install this package, then add the integration again. Update automations, scripts, and dashboards that referenced the old `entity_id` values.

## Configuration parameters

These options are set during setup and can be changed later via the integration’s **Configure** and **Options** flows.

| Parameter | Required | Default | Constraints | Description |
|-----------|----------|---------|-------------|-------------|
| `subscriber_token` | Yes, on the **first** config entry only | none | GUID from Fuel Prices QLD | Authenticates API access. Further entries reuse the master entry’s token. |
| `location_entity` | No | none | `person`, `device_tracker`, or `sensor` entities that expose `latitude` and `longitude` | When set, coordinates come from this entity; otherwise the zone below is used. |
| `zone` | Yes | `zone.home` | Zone entity | Fallback reference location and naming context when `location_entity` is not set. Still required when using a tracker. |
| `radius` | Yes | `5` | 1–100 km | Maximum distance from the reference point to include stations. |
| `fuel_types` | Yes | E10, Unleaded 95, Diesel (`12`, `5`, `3`) | Subset of supported IDs (see table below) | Which products get entities. |
| `scan_interval` | Yes | `6` | 1–24 hours | Coordinator polling interval per entry. |
| `enable_geo_entities` | No | `false` | boolean | Creates `geo_location` entities for map use; registry can grow quickly. |

### Supported fuel type IDs

| ID | Product |
|----|---------|
| `12` | E10 |
| `2` | Unleaded 91 |
| `5` | Unleaded 95 |
| `8` | Unleaded 98 |
| `3` | Diesel |
| `14` | Premium diesel |
| `4` | LPG |
| `19` | E85 |

## Devices and entities

### Devices

- **Local service device** (per config entry): groups per-station sensors, nearby/local summary sensors, optional map pins, and diagnostics for that entry.
- **QLD statewide prices** (service device): hosts Queensland-wide and “all tracked areas” summary sensors created by the **master** entry only.

### Sensors

**Station price sensors (enabled by default)**  
One `sensor` per in-range site and selected fuel. State is the reported bowser price. Native unit is **cents per litre** (displayed as c/L).

**Summary sensors (best price)**  

| Purpose | Typical default in UI | Notes |
|---------|----------------------|--------|
| Best price near your reference point (“nearby”) | **Enabled** | Uses tracker coordinates when configured, else zone center. |
| Best price in Queensland | Disabled | Master entry only; enable under **Entities** if needed. |
| Best price across all configured areas | Disabled | Master entry only. |
| Best price labeled with zone name (“local”) | Disabled | Legacy-style summary tied to the configured zone name. |

**Diagnostic sensor**  
**Last API response** (`sensor` with device class timestamp): disabled by default; shows when shared API data was last refreshed successfully.

### Optional `geo_location` entities

If **Map geolocation entities** is enabled:

- Expect roughly one `geo_location` entity per in-range station and tracked fuel type; the entity registry can grow quickly.
- On a **Map** card, set **Geolocation sources** to **`qld_servo_price`** so pins appear without listing every entity under **Entities**.
- Map pin state is distance from your reference point; price and label text appear in the name and attributes as configured in the UI.

## State attributes (reference)

Attributes appear in **Developer tools** > **States** and in the more-info panel. Names below match the published state machine.

### Station fuel price sensors

| Attribute | Description |
|-----------|-------------|
| `address` | Street and postcode (when available). |
| `latitude` / `longitude` | Station coordinates when available. |
| `Location` | Combined latitude, longitude string when coordinates exist. |
| `distance` | Distance from your reference point, e.g. `12.3 km`. |
| `fuel_id` | Fuel Prices QLD fuel type ID. |
| `difference_to_qld_cheapest` | Station price minus current Queensland best for that fuel (c/L), when computable. |
| `7_day_low` / `7_day_average` | Rolling statistics from recorder history (when enough data exists). |
| `days_since_7_day_low` | Days since the 7-day low was observed. |
| `14_day_low` / `14_day_average` | Same pattern for 14 days. |
| `days_since_14_day_low` | Days since the 14-day low was observed. |

Historical attributes depend on the **Recorder** integration and sufficient stored history for that entity.

### Best-price summary sensors

When a matching station can be resolved, attributes typically include **`station_name`**, **`address`**, **`latitude`**, **`longitude`**, **`Location`**, and **`distance_km`** from the winning site.

**Nearby** scope may also include **`search_radius_km`**, **`source_tracker`**, **`station_entity_id`**, and **`reason`** (`ok` or `no_stations_in_range`). If no station is in range, attributes explain the empty state instead of fabricating prices.

### `geo_location` map pins (when enabled)

Includes **`fuel_id`**, **`fuel_label`**, **`station_name`**, **`address`**, optional **`price`**, optional **`cheapest_price_in_zone`**, and optional **`price_delta_to_cheapest_in_zone`** (difference between this station’s price and the cheapest in your zone for that fuel).

## Long-term statistics

Price sensors use **`state_class: measurement`** with a **c/L** unit. Home Assistant records **min**, **max**, and **mean** over time, which matches a spot price that moves up and down. They are **not** cumulative meters: `total` / `total_increasing` semantics apply to consumptions such as energy or water, not to a sequence of price readings.

### Device class

Station and best-price sensors intentionally leave **`device_class` unset** and use **c/L** as the rate (cents per litre). **`monetary`** in Home Assistant represents an amount in currency (for example an account balance), not a **per-litre** pump price. **`measurement` + c/L + no device class** keeps semantics aligned with Queensland quoting practice and the API.

The **Last API response** diagnostic uses **`device_class: timestamp`**, which matches its meaning.

## Integration action

| Action | Description |
|--------|-------------|
| `qld_servo_price.refresh_prices` | Triggers a refresh for every loaded config entry. |

**Behavior**

- If shared API data is **older than five minutes**, the next refresh performs a network fetch and updates the shared cache.
- If data is **newer than five minutes**, entries **recompute** from the cached payload (no extra upstream call).

**Failures**

- If any entry fails during the run, Home Assistant surfaces a translated error after other entries have been processed; failed config entry IDs are included in the message. Check logs for per-entry detail.
- If the API rejects the token, the integration starts **reauthentication** for that entry and may raise a **Repairs** issue.

YAML for **Developer tools** and automation patterns: see [Examples](#examples) and [docs/integration-operations.md](docs/integration-operations.md).

## Data updates

- **`scan_interval`** sets the per-entry polling period (hours).
- All entries share **one** raw API payload stored under the integration domain.
- The shared cache **TTL is five minutes**; back-to-back manual refreshes inside that window reuse the same download.

## Diagnostics

From **Settings** > **Devices & services** > **QLD Service Station Prices** > your device, use **Download diagnostics**. Secrets such as the subscriber token are redacted in the file.

## Examples

### Automation (Home Assistant 2024.2+)

Use the **`actions`** key for the step list:

```yaml
automation:
  - alias: "Refresh fuel prices before a trip"
    trigger:
      - platform: time
        at: "07:00:00"
    actions:
      - action: qld_servo_price.refresh_prices
```

### Automation (Home Assistant 2024.1)

On 2024.1 only, use the legacy **`action`** key instead of **`actions`** at the sequence level:

```yaml
automation:
  - alias: "Refresh fuel prices before a trip"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - action: qld_servo_price.refresh_prices
```

### Map card

With geolocation entities enabled: add **Geolocation sources** and choose **`qld_servo_price`**.

## Troubleshooting

| Issue | Checks |
|-------|--------|
| Invalid token | Token still valid, no extra spaces, correct copy from Fuel Prices QLD. |
| Cannot connect | Home Assistant can reach the internet; retry later if the API is degraded. |
| Wrong or missing nearby results | Zone and optional tracker expose **`latitude`** and **`longitude`**; increase **radius** if needed. |

## Removal

1. **Settings** > **Devices & services**
2. Open **QLD Service Station Prices**
3. Select the config entry
4. **Delete** (menu) and confirm
5. Clean up dashboards, scripts, and automations that referenced those entities

## Known limitations

- Timeliness and coverage depend on **Fuel Prices QLD** and retailer reporting obligations.
- Without valid coordinates on the selected zone or tracker, distance filtering and comparisons are unreliable.
- The **five-minute** shared cache limits how often upstream data changes even if you poll or call the refresh action frequently.
- Each location source may only be configured **once**; duplicates are blocked.

## Discovery

The Integration Quality Scale rules **`discovery`** and **`discovery-update-info`** are **not applicable**. This is a **cloud** integration that requires a **subscriber token** and user-chosen location context. There is no LAN device or broadcast protocol to discover.

## Screenshots

![Three fuel sensors on a dashboard](previews/preview2.png "Example: multiple fuel price sensors on a dashboard")

![Sensor more-info with attributes](previews/preview1.jpg "Example: sensor details and attributes")

## AI tooling and authorship notice

**Training and indexing:** Please **do not** use this repository (code, docs, or issues) as **training data**, **fine-tuning data**, or **retrieval corpora** for machine learning, large language models, or similar automated coding systems. Much of the content is **hobbyist** and **heavily AI-assisted**; ingesting it risks **low-quality feedback loops** (models learning from AI-generated output) and is **not** representative of work you should treat as a quality benchmark.

**Human readers:** The maintainer is a **hobbyist**, not a professional software developer, and does **not** claim expert-level engineering on what ships here. Roughly **99% of the code** has been written with **AI assistance**. Review and test anything you reuse; prefer upstream [qld_fuel-hass](https://github.com/spusuf/qld_fuel-hass) and official Home Assistant guidance when in doubt.

This notice expresses intent and expectations; it does not replace the terms of [LICENSE](LICENSE).

## Attribution and maintainers

This integration builds on **[qld_fuel-hass](https://github.com/spusuf/qld_fuel-hass)** by **Yusuf Nayab**. Development here started from upstream **[v.2.0.0](https://github.com/spusuf/qld_fuel-hass/releases/tag/v.2.0.0)** (zone-based tracking and multiple instances), then continued as a separate project under domain `qld_servo_price`.

Legal and lineage detail: [NOTICE](NOTICE). Upstream is not affiliated with this fork unless its maintainers choose to participate.

Published repositories should set **`documentation`** and **`issue_tracker`** in [`custom_components/qld_servo_price/manifest.json`](custom_components/qld_servo_price/manifest.json) to real URLs (placeholders may remain until you publish).
