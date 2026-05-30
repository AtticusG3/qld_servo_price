# Agent context (qld_servo_price)

Home Assistant **custom** integration for Queensland fuel station prices (`qld_servo_price`). Declared [Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/) tier: **platinum** (`manifest.json`). Local checklist matrix: `docs/quality-scale.md`.

## Skills and rules

| Path | Use when |
|------|----------|
| `.cursor/skills/ha-integration-compliance/SKILL.md` | Quality-scale audit, PR compliance, hassfest-oriented review |
| `.cursor/rules/no-tool-branding.mdc` | Any repo content, commits, or GitHub text (no tool/vendor attribution) |

## Key paths

| Path | Purpose |
|------|---------|
| `custom_components/qld_servo_price/` | Integration code |
| `tests/components/qld_servo_price/` | Pytest suite |
| `scripts/run-tests.ps1` | Windows test runner (preferred locally) |
| `CONTRIBUTING.md` | Setup, CI, typing, coverage |
| `docs/integration-operations.md` | Actions, troubleshooting, removal |

## User preferences

- Windows-friendly commands (`.\scripts\run-tests.ps1`) over Unix-only assumptions.
- Home Assistant entity attribute style; preserve backward compatibility when changing attributes.
- Graceful logging for expected API failures (no full tracebacks).
- New integration work on a dedicated branch/worktree; avoid editing stacked PR branches in place unless asked.
- Do not edit attached plan files when implementing plans; execute against the plan as specified.
- Keep poll frequency internal (`DEFAULT_UPDATE_INTERVAL_HOURS` in `const.py`); do not expose update interval in config flow or options.
- Map UI: reuse station price data; prefer a single geolocation entity over many map markers when HA allows.
- External/GitHub prose: plain and natural; avoid em dashes that read machine-polished.
- Keep README hobbyist/assistant notice and anti-training request unless the user asks to change it.
- No tool/vendor branding in repo content, commits, or PR/issue text.

## Workspace facts

- Fork-based PRs to upstream; lineage from [spusuf/qld_fuel-hass](https://github.com/spusuf/qld_fuel-hass) (see NOTICE/README).
- Optional device-tracker location source relates to upstream issue #3; broader geo/map opt-in was declined upstream—may stay fork-only.
- Stacked PRs sometimes use a feature branch as merge base.
- HACS validation can fail on GitHub repo settings (topics/issues), not only code.
- Coverage gate 95%; full-package `mypy` per `CONTRIBUTING.md`.
- IQS `brands` assets for this custom repo: `custom_components/qld_servo_price/brand/icon.png` and `logo.png`.
- Shared helpers in `util.py`; sensor platform split across `sensor_common.py`, `sensor_station.py`, and `sensor_best_price.py`.
