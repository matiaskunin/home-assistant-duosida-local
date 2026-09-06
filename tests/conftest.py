from __future__ import annotations

import socket
import sys

import pytest

from duosida_local import ChargerIdentity, ChargerState, ChargerStatus

pytest_plugins = "pytest_homeassistant_custom_component"


if sys.platform == "win32":
    _original_socketpair = socket.socketpair
    _original_socket_type = socket.socket

    def _windows_asyncio_socketpair(*args, **kwargs):
        """Let asyncio create its loopback self-pipe while sockets are blocked."""

        guarded_socket_type = socket.socket
        socket.socket = _original_socket_type
        try:
            return _original_socketpair(*args, **kwargs)
        finally:
            socket.socket = guarded_socket_type

    socket.socketpair = _windows_asyncio_socketpair


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def identity() -> ChargerIdentity:
    return ChargerIdentity(
        device_id="0000000000000000000",
        model="DUOSIDA Mode3@32A",
        manufacturer="UCHEN",
        firmware="TEST-FIRMWARE",
    )


@pytest.fixture
def status() -> ChargerStatus:
    return ChargerStatus(
        state=ChargerState.AVAILABLE,
        raw_state=0,
        voltage=230.0,
        current=0.0,
        power=0.0,
        total_energy=250.0,
        session_energy=0.0,
        station_temperature=28.0,
        cp_voltage=12.0,
        vehicle_connected=False,
        sequence=1,
    )
