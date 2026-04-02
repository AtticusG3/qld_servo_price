## Learned User Preferences
- Prefer Windows-compatible workflows and command/script formats over Unix-only hooks.
- Prefer Home Assistant-style entity attributes while preserving backward compatibility.
- Do not add tool/vendor branding text in repo content, commit messages, or PR/comment text.
- Prefer graceful logging for expected upstream failures in services (for example API errors) without emitting full tracebacks.
- Prefer isolating new integration work in a dedicated branch (often in a separate git worktree) rather than modifying stacked PR branches in place unless explicitly requested.
- For map or geolocation presentation, prefer reusing existing station price data and minimizing duplicate entity surfaces (for example favoring a single geolocation source over listing many per-station entities on the Map card) when Home Assistant capabilities allow.
- When drafting user-facing external text (for example GitHub replies), prefer plain, natural phrasing; avoid stylized punctuation such as em dashes when it reads as overly polished or machine-generated.

## Learned Workspace Facts
- The workspace is a Home Assistant custom integration repository (domain `qld_servo_price`) for Queensland fuel station prices.
- Contributor setup, tests, typing, and CI are described in `CONTRIBUTING.md`.
- The user maintains and contributes changes upstream via fork-based GitHub pull requests.
- Optional location-source behavior and related discussion trace in part to upstream spusuf/qld_fuel-hass issue #3 (device-tracker-style coordinates in addition to zones); broader geo or map opt-in pull requests have been declined upstream, so similar features may remain fork-only or custom-repo unless upstream changes direction.
- Stacked pull requests may use a feature branch as the merge base when later work depends on earlier in-flight changes.
- HACS repository validation can fail on GitHub repository settings (for example topics and issues) rather than integration code alone.
- Use `scripts/run-tests.ps1` to run the project test suite on Windows when available.
