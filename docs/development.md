# Development and releases

The integration supports Home Assistant 2026.8.0 or newer and is tested against
the latest 2026.8 patch used by CI. Runtime code stays inside
`custom_components/duosida_local`; the only external runtime requirement is an
exactly pinned `duosida-local` GitHub tag.

## Release order

1. Complete library checks and publish an immutable GitHub tag named
   `v0.1.0aN`. Do not publish it to PyPI during physical validation.
2. Update the exact Git tag in the manifest and the integration version to the
   same alpha.
3. Run Ruff, MyPy, Pytest, Hassfest and HACS validation.
4. Create the integration GitHub pre-release.
5. Install that release through HACS on the test instance and update the
   physical matrix.

No release script commits or pushes automatically. The maintainer reviews and
runs the documented Git commands.

## Windows note

Home Assistant itself targets Linux and imports the POSIX-only `fcntl` module.
For local unit tests on Windows, prepend the test-only shim:

```powershell
$env:PYTHONPATH = "tests\windows_stubs;."
$env:UV_CACHE_DIR = ".uv-cache"
uv run pytest -p no:cacheprovider
```

Ubuntu CI does not use this shim and validates against the real POSIX module.
The integration CI checks out the matching library tag beside this repository,
which preserves the same sibling layout used by the local workspace.

For local development, clone both repositories into sibling directories. The
`[tool.uv.sources]` override uses `../duosida-local`, so edits can be tested
together without copying library code into the integration repository. The
production Home Assistant manifest uses the public Git tag instead.
