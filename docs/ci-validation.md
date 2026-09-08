# CI validation record

## English

The integration locks its development dependency to the same immutable
`duosida-local` Git tag declared by `manifest.json`. CI installs that lockfile
in a clean checkout and rejects any drift with `uv sync --locked --all-groups`.

The release-metadata test verifies the manifest tag, the direct Git dependency,
the installed distribution version and the pinned uv version together. The
config flow imports Home Assistant's `network` integration, which is declared
in the manifest so Hassfest can load the dependency before setup.

Dependabot updates Home Assistant and its custom-component test plugin as one
compatibility unit. Pytest remains pinned to the exact version required by that
plugin.

## Español

La integración bloquea su dependencia de desarrollo al mismo tag Git inmutable
de `duosida-local` declarado por `manifest.json`. CI instala ese lockfile en un
checkout limpio y rechaza cualquier diferencia con `uv sync --locked --all-groups`.

La prueba de metadatos de release verifica conjuntamente el tag del manifiesto,
la dependencia Git directa, la versión instalada y la versión fijada de uv. El
config flow importa la integración `network` de Home Assistant, declarada en el
manifiesto para que Hassfest pueda cargarla antes del setup.

Dependabot actualiza Home Assistant y su plugin de tests como una unidad de
compatibilidad. Pytest permanece fijado a la versión exacta requerida por ese
plugin.
