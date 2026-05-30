# Changelog

All notable changes to this project are documented in this file.

## [2.1.0] - 2026-05-30

### Added

- Shared `util.py` helpers and sensor platform modules (`sensor_common`, `sensor_station`, `sensor_best_price`).
- Gold/platinum Integration Quality Scale documentation (`docs/quality-scale.md`).
- `test_loaders.register_real_util_module()` for importlib-based unit tests.
- Integration brand assets under `custom_components/qld_servo_price/brand/`.

### Changed

- Declared Integration Quality Scale tier: **platinum** (`manifest.json`).
- Coordinator refresh logging is shared at domain scope (throttled outage warnings).
- Config flow and options no longer expose update interval; polling uses internal `DEFAULT_UPDATE_INTERVAL_HOURS` (6).
- README and operations docs updated for fixed polling and HA 2026.3+ branding.

### Fixed

- Thread-safe scheduling for location listener updates.
- Entity availability when coordinator refresh fails.

### Notes

- Legacy `scan_interval` stored on existing config entries is ignored; all entries poll every six hours.
- Requires Home Assistant 2024.1+; custom branding in Settings needs 2026.3+.

## [2.0.0] - 2026-04-02

Initial major release under domain `qld_servo_price` (fork lineage from upstream qld_fuel-hass v2.0.0).
