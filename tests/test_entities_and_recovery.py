from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest
from custom_components.duosida_local import _async_reload_entry, async_unload_entry
from custom_components.duosida_local.binary_sensor import (
    BINARY_SENSORS,
    DuosidaBinarySensor,
)
from custom_components.duosida_local.button import BUTTONS, DuosidaButton
from custom_components.duosida_local.const import DOMAIN
from custom_components.duosida_local.coordinator import DuosidaCoordinator
from custom_components.duosida_local.number import DuosidaMaxCurrent
from custom_components.duosida_local.runtime import DuosidaRuntimeData
from custom_components.duosida_local.sensor import (
    IDENTITY_SENSORS,
    SENSORS,
    DuosidaIdentitySensor,
    DuosidaSensor,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from duosida_local import (
    ChargerIdentity,
    ChargerStatus,
    DuosidaConnectionError,
)


class ScriptedClient:
    """Small protocol client double used for coordinator unit tests."""

    host = "192.0.2.10"

    def __init__(self, identity: ChargerIdentity, status: ChargerStatus) -> None:
        self.identity = identity
        self.status = status
        self.connected = False
        self.disconnect_calls = 0
        self.state_calls = 0
        self.recovered = asyncio.Event()
        self.park = asyncio.Event()
        self.start_charging = AsyncMock()
        self.stop_charging = AsyncMock()
        self.set_max_current = AsyncMock()

    async def connect(self) -> ChargerIdentity:
        self.connected = True
        return self.identity

    async def disconnect(self) -> None:
        self.connected = False
        self.disconnect_calls += 1

    async def states(self) -> AsyncIterator[ChargerStatus]:
        self.state_calls += 1
        if self.state_calls <= 9:
            raise DuosidaConnectionError("offline")
        if self.state_calls == 10:
            yield self.status
            return
        self.recovered.set()
        await self.park.wait()
        if False:  # pragma: no cover - makes this an async generator
            yield self.status


def _runtime_entry(
    hass: HomeAssistant,
    identity: ChargerIdentity,
    status: ChargerStatus,
) -> tuple[MockConfigEntry, ScriptedClient, DuosidaCoordinator]:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=identity.device_id,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 9988},
    )
    entry.add_to_hass(hass)
    client = ScriptedClient(identity, status)
    coordinator = DuosidaCoordinator(hass, entry, client)  # type: ignore[arg-type]
    entry.runtime_data = DuosidaRuntimeData(client, coordinator, identity)  # type: ignore[arg-type]
    return entry, client, coordinator


async def test_entities_without_data_and_command_errors(
    hass: HomeAssistant,
    identity: ChargerIdentity,
    status: ChargerStatus,
) -> None:
    entry, client, _coordinator = _runtime_entry(hass, identity, status)
    assert DuosidaSensor(entry, SENSORS[0]).native_value is None
    assert DuosidaBinarySensor(entry, BINARY_SENSORS[0]).is_on is None
    assert DuosidaIdentitySensor(entry, IDENTITY_SENSORS[0]).native_value == identity.device_id

    client.start_charging.side_effect = DuosidaConnectionError("offline")
    with pytest.raises(HomeAssistantError):
        await DuosidaButton(entry, BUTTONS[0]).async_press()

    number = DuosidaMaxCurrent(entry)
    assert number.extra_state_attributes == {}
    with pytest.raises(HomeAssistantError):
        await number.async_set_native_value(6.5)
    client.set_max_current.side_effect = DuosidaConnectionError("offline")
    with pytest.raises(HomeAssistantError):
        await number.async_set_native_value(6)


async def test_coordinator_initial_errors_and_shutdown_without_task(
    hass: HomeAssistant,
    identity: ChargerIdentity,
    status: ChargerStatus,
) -> None:
    _entry, client, coordinator = _runtime_entry(hass, identity, status)
    client.connect = AsyncMock(side_effect=DuosidaConnectionError("offline"))
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    client.connect = AsyncMock(return_value=identity)

    async def empty_states() -> AsyncIterator[ChargerStatus]:
        if False:  # pragma: no cover - makes this an async generator
            yield status

    client.states = empty_states  # type: ignore[method-assign]
    with pytest.raises(UpdateFailed, match="stream ended"):
        await coordinator._async_update_data()
    await coordinator.async_shutdown()
    assert client.disconnect_calls == 1


async def test_coordinator_reconnects_and_manages_repair_issue(
    hass: HomeAssistant,
    identity: ChargerIdentity,
    status: ChargerStatus,
) -> None:
    _entry, client, coordinator = _runtime_entry(hass, identity, status)
    with (
        patch("custom_components.duosida_local.coordinator.asyncio.sleep", new=AsyncMock()),
        patch("custom_components.duosida_local.coordinator.ir.async_create_issue") as create_issue,
        patch("custom_components.duosida_local.coordinator.ir.async_delete_issue") as delete_issue,
    ):
        task = hass.async_create_task(coordinator._async_stream_with_reconnect())
        await client.recovered.wait()
        assert coordinator.data == status
        create_issue.assert_called_once()
        delete_issue.assert_called_once()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


async def test_unload_failure_and_reload(
    hass: HomeAssistant,
    identity: ChargerIdentity,
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=identity.device_id,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 9988},
    )
    entry.add_to_hass(hass)
    with patch.object(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=False)):
        assert not await async_unload_entry(hass, entry)  # type: ignore[arg-type]
    with patch.object(hass.config_entries, "async_reload", AsyncMock()) as reload_entry:
        await _async_reload_entry(hass, entry)  # type: ignore[arg-type]
    reload_entry.assert_awaited_once_with(entry.entry_id)
