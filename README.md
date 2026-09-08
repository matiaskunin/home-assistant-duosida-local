# Duosida Local for Home Assistant

[![CI](https://github.com/matiaskunin/home-assistant-duosida-local/actions/workflows/ci.yml/badge.svg)](https://github.com/matiaskunin/home-assistant-duosida-local/actions/workflows/ci.yml)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![License: GPL-3.0-only](https://img.shields.io/badge/license-GPL--3.0--only-blue.svg)](LICENSE)

A local-push Home Assistant integration for verified Duosida EV chargers. It
uses [`duosida-local`](https://github.com/matiaskunin/duosida-local) and does not
depend on DSCharge or cloud services at runtime.

> **Alpha:** telemetry is capture-verified on one SES-32-ORW. Start, stop,
> current setting and UDP discovery must complete the documented physical test
> matrix before a stable release.

Spanish guide: [Guía en español](docs/es/README.md).

## Compatibility

The initial target is DUOSIDA SES-32-ORW: single phase, 230 V, 32 A, 7.2 kW.
Other Duosida models remain explicitly unverified.

## Install with HACS

Until the repository is accepted into HACS defaults:

1. In HACS, open **Integrations** and choose **Custom repositories**.
2. Add `https://github.com/matiaskunin/home-assistant-duosida-local` as an
   **Integration** repository.
3. Download the matching alpha release and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration**.
5. Search for **Duosida Local**.
6. Try LAN discovery or enter the charger IP manually.

The matching `duosida-local` alpha is installed by Home Assistant directly from
its public GitHub tag. It is not published to PyPI during physical validation.
HACS downloads this integration; Home Assistant then processes `manifest.json`
and installs the pinned library requirement.

## Entities

| Entity | Type | Notes |
|---|---|---|
| State | Sensor | Raw code also available as disabled diagnostic |
| Voltage / current / power | Sensors | Push telemetry |
| Total / session energy | Sensors | Local kWh register; optional lifetime offset |
| Station temperature | Sensor | Native °C; display unit follows Home Assistant |
| Vehicle connected / charging | Binary sensors | Connection uses the measured CP voltage |
| Start / stop charging | Buttons | Require observed state confirmation |
| Maximum current | Number, 6–32 A | Assumed state; decimal write-only protocol |
| CP voltage | Disabled diagnostic sensor | Useful for protocol validation |
| Identifier / model / manufacturer / firmware | Disabled diagnostic sensors | Static technical data |

## Local-only verification

The integration opens TCP 9988 to the configured LAN host. Discovery uses UDP
48890/48899. There are no HTTP cloud endpoints, credentials or analytics in the
source. See [Security and network isolation](docs/security.md).

## Development

```powershell
uv sync --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

See [development](docs/development.md), [physical testing](docs/physical-testing.md)
and [troubleshooting](docs/troubleshooting.md). Architecture and safe automation
examples are documented in [architecture](docs/architecture.md) and
[automations](docs/automations.md). Research references and clean-room boundaries
are listed in [sources](docs/sources.md); release changes are in the
[changelog](CHANGELOG.md). Sanitized real-device findings are recorded in the
[physical validation reports](docs/validation/2026-09-07-first-home-assistant-test.md).

## Remove

1. Open **Settings → Devices & services → Duosida Local**.
2. Delete the charger config entry and wait for its entities to unload.
3. Remove the integration in HACS and restart Home Assistant.

Unloading cancels reconnect work and closes the TCP connection before HACS
removes the files.

## HACS defaults status

Alpha releases are intended for a HACS custom repository. The automated HACS
check temporarily ignores only `brands`, because no original charger photograph
or unreviewed trademark asset will be published. Inclusion in HACS defaults
requires reviewed assets in `home-assistant/brands`, a public release and a
validation run without ignores.

## License

Copyright (C) 2026 Matias Kunin. Licensed under `GPL-3.0-only`.
