# Integration operations

Operational detail for **QLD Service Station Prices** (`qld_servo_price`). User-facing installation, entities, and behavior are summarized in the repository [README.md](../README.md).

## Integration action

The integration registers one action (service):

| Action | Purpose |
|--------|---------|
| `qld_servo_price.refresh_prices` | Request an immediate refresh for all loaded config entries |

### Developer Tools (YAML)

```yaml
action: qld_servo_price.refresh_prices
data: {}
```

Use **Developer tools > Actions** in Home Assistant; the YAML above matches the action identifier and empty `data` object.

### Automation compatibility

Automations should list steps under the `actions` key on **Home Assistant 2024.2 and later**. On **2024.1**, use the legacy `action` key at the automation sequence level. See [README.md](../README.md#examples) for a copy-paste example.

## Troubleshooting

| Symptom | What to check |
|---------|----------------|
| Invalid token during setup | Token is current, copied exactly, no leading or trailing spaces |
| Cannot connect | Home Assistant outbound internet; retry later for upstream outages |
| No nearby stations | Increase radius; confirm zone or tracked entity exposes latitude and longitude |
| Stale values | Call `qld_servo_price.refresh_prices`; remember the shared 5-minute API cache (see README) |
| Repairs / reauth | Supply a new Data Consumer Token when the API rejects the stored token |

## Known limitations (operations)

- Data is only as current as the Queensland fuel price API and retailer reporting rules allow.
- All config entries share one cached API payload at the integration level (short freshness window).
- Each distinct location source (zone or tracked entity) may only be used once; duplicates are rejected by unique ID rules.

## Removal

1. **Settings** > **Devices & services**
2. Open **QLD Service Station Prices**
3. Select the config entry
4. **Delete** (menu) and confirm
5. Remove dashboards, scripts, and automations that referenced those entities if desired

## Developer resources

- Fuel Prices QLD developer area: [fuelpricesqld.com.au](https://www.fuelpricesqld.com.au/#developers)
- Postman collection: [postmanv1.json](https://www.fuelpricesqld.com.au/documents/postmanv1.json)
- API reference (this repo): [fuel-prices-qld-api-reference.md](./fuel-prices-qld-api-reference.md)
- Published API PDF: [FuelPricesQLDDirectAPI(OUT)v1.6.pdf](https://www.fuelpricesqld.com.au/documents/FuelPricesQLDDirectAPI(OUT)v1.6.pdf)

## Local testing (Windows)

```powershell
.\scripts\run-tests.ps1 -Install
.\scripts\run-tests.ps1
```

Equivalent manual steps and coverage commands are documented in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Coverage artifacts in CI

The GitHub Actions workflow **Test Coverage** runs pytest with `pytest-cov` and uploads:

- `coverage.xml`
- `coverage-summary.txt`

Download them from the workflow run’s artifacts when you need machine- or human-readable coverage evidence.

If installing dev dependencies fails on Windows (for example building `greenlet`), align Python version and architecture with wheels published for your platform, or update the MSVC build tools as needed.
