"""Minimal Windows-only import shim for Home Assistant's POSIX runner tests.

This directory is added to PYTHONPATH only by the documented local Windows test
command. Linux CI uses the standard-library fcntl module.
"""

LOCK_EX = 2
LOCK_NB = 4
LOCK_UN = 8


def flock(_fd: int, _operation: int) -> None:
    """No-op because unit tests do not exercise the process lock runner."""
