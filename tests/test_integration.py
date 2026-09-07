from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

from custom_components.duosida_local.const import CONF_ENERGY_OFFSET, DOMAIN
from custom_components.duosida_local.diagnostics import async_get_config_entry_diagnostics
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from duosida_local import (
    ChargerIdentity,
    ChargerState,
    ChargerStatus,
    CommandReceipt,
    CommandStatus,
    DuosidaConnectionError,
)


class FakeClient:
    def __init__(self, identity: ChargerIdentity, status: ChargerStatus) -> None:
        self.host = "192.0.2.10"
        self.identity = identity
        self.status = status
        self.connected = False
        self.disconnect_calls = 0
        self.start_charging = AsyncMock(
            return_value=CommandReceipt(
                "start", CommandStatus.CONFIRMED, 2, observed_state=ChargerState.CHARGING
            )
        )
        self.stop_charging = AsyncMock(
            return_value=CommandReceipt(
                "stop", CommandStatus.CONFIRMED, 3, observed_state=ChargerState.FINISHED
            )
        )
        self.set_max_current = AsyncMock(
            return_value=CommandReceipt(
                "set_max_current", CommandStatus.SENT_UNCONFIRMED, 4, requested_value=6
            )
        )
        self._updates: asyncio.Queue[ChargerStatus | BaseException] = asyncio.Queue()

    async def connect(self) -> ChargerIdentity:
        self.connected = True
        return self.identity

    async def disconnect(self) -> None:
        self.connected = False
        self.disconnect_calls += 1

    async def states(self) -> AsyncIterator[ChargerStatus]:
        yield self.status
        while self.connected:
            item = await self._updates.get()
            if isinstance(item, BaseException):
                raise item
            yield item


async def _setup_entry(
    hass: HomeAssistant,
    identity: ChargerIdentity,
    status: ChargerStatus,
    *,
    energy_offset: float = 0.0,
) -> tuple[MockConfigEntry, FakeClient]:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Duosida test",
        unique_id=identity.device_id,
        data={
            CONF_HOST: "192.0.2.10",
            CONF_PORT: 9988,
            CONF_ENERGY_OFFSET: energy_offset,
        },
    )
    entry.add_to_hass(hass)
    client = FakeClient(identity, status)
    with patch("custom_components.duosida_local.DuosidaClient", return_value=client):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, client


async def test_setup_entities_commands_diagnostics_and_unload(
    hass: HomeAssistant, identity: ChargerIdentity, status: ChargerStatus
) -> None:
    entry, client = await _setup_entry(hass, identity, status)
    registry = er.async_get(hass)

    voltage_id = registry.async_get_entity_id("sensor", DOMAIN, f"{identity.device_id}_voltage")
    assert voltage_id is not None
    assert (voltage_state := hass.states.get(voltage_id)) is not None
    assert voltage_state.state == "230.0"

    connected_id = registry.async_get_entity_id(
        "binary_sensor", DOMAIN, f"{identity.device_id}_vehicle_connected"
    )
    assert connected_id is not None
    assert (connected_state := hass.states.get(connected_id)) is not None
    assert connected_state.state == "off"

    current_id = registry.async_get_entity_id("number", DOMAIN, f"{identity.device_id}_max_current")
    assert current_id is not None
    await hass.services.async_call(
        "number", "set_value", {"entity_id": current_id, "value": 6}, blocking=True
    )
    client.set_max_current.assert_awaited_once_with(6)
    assert (current_state := hass.states.get(current_id)) is not None
    assert current_state.attributes["command_status"] == "sent_unconfirmed"

    start_id = registry.async_get_entity_id("button", DOMAIN, f"{identity.device_id}_start")
    stop_id = registry.async_get_entity_id("button", DOMAIN, f"{identity.device_id}_stop")
    assert start_id and stop_id
    await hass.services.async_call("button", "press", {"entity_id": start_id}, blocking=True)
    await hass.services.async_call("button", "press", {"entity_id": stop_id}, blocking=True)
    client.start_charging.assert_awaited_once()
    client.stop_charging.assert_awaited_once()

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostics["entry"]["unique_id"] == "**REDACTED**"
    assert diagnostics["entry"]["data"][CONF_HOST] == "**REDACTED**"
    assert diagnostics["identity"]["device_id"] == "**REDACTED**"
    assert diagnostics["status"]["voltage"] == 230.0

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert client.disconnect_calls >= 1


async def test_push_update_changes_entities(
    hass: HomeAssistant, identity: ChargerIdentity, status: ChargerStatus
) -> None:
    entry, client = await _setup_entry(hass, identity, status)
    charging = ChargerStatus(
        state=ChargerState.CHARGING,
        raw_state=2,
        voltage=225.0,
        current=6.9,
        power=1552.5,
        total_energy=251.0,
        session_energy=0.1,
        station_temperature=30.0,
        cp_voltage=6.0,
        vehicle_connected=True,
        sequence=2,
    )
    await client._updates.put(charging)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    charging_id = registry.async_get_entity_id(
        "binary_sensor", DOMAIN, f"{identity.device_id}_charging"
    )
    assert charging_id is not None
    assert (charging_state := hass.states.get(charging_id)) is not None
    assert charging_state.state == "on"
    await hass.config_entries.async_unload(entry.entry_id)


async def test_total_energy_applies_configured_lifetime_offset(
    hass: HomeAssistant, identity: ChargerIdentity, status: ChargerStatus
) -> None:
    entry, _client = await _setup_entry(hass, identity, status, energy_offset=12_768.0125)
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{identity.device_id}_total_energy")
    assert entity_id is not None
    assert (energy_state := hass.states.get(entity_id)) is not None
    assert float(energy_state.state) == 13_018.0125
    await hass.config_entries.async_unload(entry.entry_id)


async def test_setup_failure_is_retryable(
    hass: HomeAssistant, identity: ChargerIdentity, status: ChargerStatus
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=identity.device_id,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 9988},
    )
    entry.add_to_hass(hass)
    client = FakeClient(identity, status)
    client.connect = AsyncMock(side_effect=DuosidaConnectionError("offline"))
    with patch("custom_components.duosida_local.DuosidaClient", return_value=client):
        assert not await hass.config_entries.async_setup(entry.entry_id)
    assert client.disconnect_calls == 1
