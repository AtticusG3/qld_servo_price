# Integration Quality Scale (qld_servo_price)

Declared in `manifest.json`: **gold**.

Official references: [overview](https://developers.home-assistant.io/docs/core/integration-quality-scale/), [rules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules), [checklist](https://developers.home-assistant.io/docs/core/integration-quality-scale/checklist). Core integrations also maintain `quality_scale.yaml`; this custom repo uses this file plus README for exemptions.

This matrix reflects the custom integration repository (in-repo README/docs, local `brand/` assets). Rules marked N/A are documented in [README.md](../README.md#discovery).

## Bronze

| Rule | Status | Evidence |
|------|--------|----------|
| action-setup | pass | `refresh_prices` registered in `__init__.py` |
| appropriate-polling | pass | Per-entry `scan_interval`; shared 5-minute API cache in `coordinator.py` |
| brands | pass | `custom_components/qld_servo_price/brand/icon.png`, `logo.png` (HA 2026.3+) |
| common-modules | pass | `util.py`, `sensor_common.py` shared across platforms |
| config-flow-test-coverage | pass | `tests/components/qld_servo_price/test_config_flow.py` |
| config-flow | pass | `config_flow.py`, `strings.json`, `data_description` |
| dependency-transparency | pass | Empty `requirements` in manifest; uses HA stack |
| docs-actions | pass | README integration action section |
| docs-high-level-description | pass | README introduction |
| docs-installation-instructions | pass | README installation |
| docs-removal-instructions | pass | README removal |
| entity-event-setup | pass | `async_added_to_hass`, coordinator listeners |
| entity-unique-id | pass | All entities set `unique_id` |
| has-entity-name | pass | `_attr_has_entity_name = True` |
| runtime-data | pass | `entry.runtime_data = coordinator` |
| test-before-configure | pass | `async_validate_token` in config flow |
| test-before-setup | pass | `async_config_entry_first_refresh` before platforms |
| unique-config-entry | pass | Location-based unique ID + abort |

## Silver

| Rule | Status | Evidence |
|------|--------|----------|
| action-exceptions | pass | Translated `HomeAssistantError` on refresh failures |
| config-entry-unloading | pass | `async_unload_entry` |
| docs-configuration-parameters | pass | README configuration table |
| docs-installation-parameters | pass | README requirements |
| entity-unavailable | pass | `CoordinatorEntity`; test `test_coordinator_entities_unavailable_when_update_fails` |
| integration-owner | pass | `codeowners` in manifest |
| log-when-unavailable | pass | Domain `refresh_log` in coordinator |
| parallel-updates | pass | `PARALLEL_UPDATES = 1` on sensor/geo platforms |
| reauthentication-flow | pass | `async_step_reauth` / `async_step_reauth_confirm` |
| test-coverage | pass | >=95% coverage via `scripts/run-tests.ps1` |

## Gold

| Rule | Status | Evidence |
|------|--------|----------|
| devices | pass | `DeviceInfo` on sensor/geo entities |
| diagnostics | pass | `diagnostics.py` + tests |
| discovery-update-info | N/A | Cloud/token integration; no discovery protocol |
| discovery | N/A | Same as above |
| docs-data-update | pass | README data updates |
| docs-examples | pass | README automation examples |
| docs-known-limitations | pass | README known limitations |
| docs-supported-devices | pass | README fuel types / service devices |
| docs-supported-functions | pass | README entities and actions |
| docs-troubleshooting | pass | README troubleshooting |
| docs-use-cases | pass | README what you get / map |
| dynamic-devices | pass | Entities added/removed by radius and fuel list |
| entity-category | pass | Diagnostic category on summary sensors |
| entity-device-class | pass | Timestamp diagnostic; price sensors documented as c/L |
| entity-disabled-by-default | pass | Global/tracked/local/last-api defaults |
| entity-translations | pass | `strings.json`, `translations/en.json` |
| exception-translations | pass | `exceptions` in strings + coordinator/service |
| icon-translations | pass | `icons.json` |
| reconfiguration-flow | pass | `async_step_reconfigure` |
| repair-issues | pass | Auth/connectivity issues in coordinator |
| stale-devices | pass | Stale entity cleanup; `async_remove_config_entry_device` |

## Platinum

| Rule | Status | Evidence |
|------|--------|----------|
| async-dependency | pass | Async `aiohttp` via HA client session |
| inject-websession | pass | `async_get_clientsession(hass)` |
| strict-typing | pass | `mypy.ini` strict; CI typing workflow |

## Achieved tier

**Gold** (custom repo, in-repo documentation). **Platinum** typing/HTTP rules also pass locally.
