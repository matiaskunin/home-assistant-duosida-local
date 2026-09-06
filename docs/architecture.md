# Architecture

```text
GitHub: home-assistant-duosida-local
  └─ HACS downloads custom_components/duosida_local
       └─ Home Assistant reads manifest.json
            └─ installs the exact duosida-local GitHub tag
                 └─ integration imports the public duosida_local API

ConfigEntry.runtime_data
  ├─ DuosidaClient (one persistent TCP connection, library repository)
  ├─ DuosidaCoordinator (HA lifecycle and reconnect/backoff)
  └─ ChargerIdentity (immutable device metadata)
       └─ coordinator entities (properties perform no I/O)
```

The config flow probes TCP before saving and uses the charger identifier as the
stable config-entry unique ID. If discovery finds a known charger at a new IP,
Home Assistant updates the existing entry instead of creating a duplicate.

The coordinator performs the first status read, owns exactly one background
stream task and converts library errors into Home Assistant availability. It
disconnects before each bounded reconnect attempt, logs through the coordinator
instead of producing repeated warnings, and creates a translated repair issue
after five failures. A successful fresh snapshot clears the issue.

All platforms share the coordinator snapshot. Entity properties are pure reads;
only button presses and number changes call the library. The library serializes
wire commands, so Home Assistant also limits write-platform parallelism to one.

The integration has no cloud, HTTP, credential or analytics client. The exact
library Git tag is pinned in `manifest.json` and kept aligned with the
integration alpha version. The two repositories do not copy source code: the
integration depends only on the library's public Python API.

During physical validation, Home Assistant needs Internet access once to fetch
the public GitHub dependency during installation or upgrade. Charger
communication remains local and continues without WAN access after the
requirement is installed.
