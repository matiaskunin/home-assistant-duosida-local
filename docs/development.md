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
   Update the Git dependency in `pyproject.toml` to the same tag and regenerate
   the lockfile with `uv lock`. Then verify `uv sync --locked --all-groups` in a
   clean checkout. The lockfile resolves the immutable Git tag, not a sibling
   development directory.
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
$env:PYTHONPATH = "tests\windows_stubs"
$env:UV_CACHE_DIR = ".uv-cache"
uv run pytest -p no:cacheprovider
```

Ubuntu CI does not use this shim and validates against the real POSIX module.
Pytest adds the repository root through `pythonpath = ["."]` in
`pyproject.toml`, so `custom_components` imports do not depend on a shell's
`PYTHONPATH` setting on either platform.
For normal work, `uv sync --locked --all-groups` installs the exact library tag
recorded in `pyproject.toml`. To exercise uncommitted library edits without
changing the integration lockfile, clone both repositories as siblings and run
the desired command with a temporary editable override, for example:

```powershell
uv run --with-editable ..\duosida-local pytest
```

Do not commit a local-path source or a lockfile generated from one. The
production manifest and CI both resolve the same immutable public Git tag.
