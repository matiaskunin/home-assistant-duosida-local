"""Minimal Windows-only resource shim for Home Assistant unit-test imports."""

RLIMIT_NOFILE = 7


def getrlimit(_resource: int) -> tuple[int, int]:
    """Return a harmless test-only descriptor limit."""

    return (2048, 2048)


def setrlimit(_resource: int, _limits: tuple[int, int]) -> None:
    """No-op because Windows does not expose POSIX resource limits."""
