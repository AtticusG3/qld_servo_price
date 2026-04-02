# Contributing

This repository is a Home Assistant custom integration (`qld_servo_price`). The following notes are for anyone changing code, tests, or packaging.

## Repository layout

| Path | Purpose |
|------|---------|
| `custom_components/qld_servo_price/` | Integration package (manifest, config flow, platforms, coordinator) |
| `tests/components/qld_servo_price/` | Pytest suite for the integration |
| `docs/` | API reference and operational supplements |
| `scripts/run-tests.ps1` | Windows-oriented test runner (venv + deps + pytest) |
| `.github/workflows/` | CI (tests, coverage, typing, hassfest, validation) |

## Prerequisites

- Python **3.12** (matches CI; the test script defaults to 3.12 on Windows).
- Git.

Optional: Home Assistant core checkout if you run `hassfest` locally against full core tooling.

## Running tests

### Windows (recommended)

From the repository root:

```powershell
.\scripts\run-tests.ps1 -Install   # first-time: create .venv and install dev deps
.\scripts\run-tests.ps1            # subsequent runs
```

### Any platform (manual)

```text
python -m venv .venv
.venv\Scripts\python.exe -m pip install -U pip          # Windows
# source .venv/bin/activate && pip install -U pip         # Linux / macOS
pip install -r requirements-dev.txt
python -m pytest -q tests/components/qld_servo_price
```

`pytest.ini` enables coverage for `custom_components/qld_servo_price` with `--cov-fail-under=95`.

### Local coverage report

Single line (any shell):

```text
python -m pytest -q tests/components/qld_servo_price --cov=custom_components/qld_servo_price --cov-report=term-missing --cov-report=xml:coverage.xml
```

## Static typing

The **Type Check** workflow runs:

```text
python -m mypy --config-file mypy.ini custom_components/qld_servo_price
```

Run the same command before pushing. The **Test Coverage** workflow also runs a narrower mypy step on `diagnostics.py` only; full-package typing is gated by `typing.yml`.

## CI overview

| Workflow | Role |
|----------|------|
| Test Coverage | Pytest with coverage threshold; uploads `coverage.xml` and `coverage-summary.txt` |
| Type Check | Full-package mypy |
| hassfest | Integration manifest / metadata checks |
| validate | Additional repository validation |

## Documentation

- End-user and integration overview: [README.md](README.md)
- Operations, troubleshooting, and CI artifacts: [docs/integration-operations.md](docs/integration-operations.md)
- Fuel Prices QLD API (contributors): [docs/fuel-prices-qld-api-reference.md](docs/fuel-prices-qld-api-reference.md)

When you change behavior, config options, entities, or actions, update the README (and `docs/` if the change is operational or API-related).

## Integration quality

`manifest.json` declares `quality_scale`: **gold**, aligned with the [Home Assistant Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/). Changes should preserve existing checklist expectations (config flow, diagnostics, translated exceptions, tests, and documentation parity).

## Licensing and attribution

See [LICENSE](LICENSE) and [NOTICE](NOTICE). The integration originated from
[Yusuf Nayab's qld_fuel-hass](https://github.com/spusuf/qld_fuel-hass), baseline
[upstream v.2.0.0](https://github.com/spusuf/qld_fuel-hass/releases/tag/v.2.0.0).
