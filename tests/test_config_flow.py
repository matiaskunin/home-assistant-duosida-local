from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from custom_components.duosida_local.config_flow import _async_discover_chargers, _async_probe
from custom_components.duosida_local.const import CONF_ENERGY_OFFSET, DOMAIN
from homeassistant.config_entries import SOURCE_RECONFIGURE
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from duosida_local import (
    DiscoveredCharger,
    DuosidaConnectionError,
    DuosidaProtocolError,
)


@pytest.fixture(autouse=True)
def mock_setup_entry():
    """Prevent a newly created flow entry from contacting a real charger."""

    with patch(
        "custom_components.duosida_local.async_setup_entry",
        AsyncMock(return_value=True),
    ) as setup_entry:
        yield setup_entry


async def test_user_menu(hass) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["discover", "manual"]


async def test_manual_success(hass, identity) -> None:
    with patch(
        "custom_components.duosida_local.config_flow._async_probe",
        AsyncMock(return_value=identity),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "manual"}, data={CONF_HOST: "192.0.2.10", CONF_PORT: 9988}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Duosida DUOSIDA Mode3@32A"
    assert result["data"] == {
        CONF_HOST: "192.0.2.10",
        CONF_PORT: 9988,
        CONF_ENERGY_OFFSET: 0.0,
    }


async def test_manual_connection_error(hass) -> None:
    with patch(
        "custom_components.duosida_local.config_flow._async_probe",
        AsyncMock(side_effect=DuosidaConnectionError),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "manual"}, data={CONF_HOST: "192.0.2.10", CONF_PORT: 9988}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_manual_protocol_and_unknown_errors(hass) -> None:
    for exception, expected in (
        (DuosidaProtocolError("invalid"), "invalid_response"),
        (RuntimeError("unexpected"), "unknown"),
    ):
        with patch(
            "custom_components.duosida_local.config_flow._async_probe",
            AsyncMock(side_effect=exception),
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "manual"},
                data={CONF_HOST: "192.0.2.10", CONF_PORT: 9988},
            )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": expected}


async def test_discovery_form_and_success(hass, identity) -> None:
    devices = (DiscoveredCharger("192.0.2.10", device_id=identity.device_id),)
    with (
        patch(
            "custom_components.duosida_local.config_flow.discover_chargers",
            AsyncMock(return_value=devices),
        ),
        patch(
            "custom_components.duosida_local.config_flow._async_probe",
            AsyncMock(return_value=identity),
        ),
    ):
        form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "discover"})
        result = await hass.config_entries.flow.async_configure(
            form["flow_id"], {CONF_HOST: "192.0.2.10"}
        )
        await hass.async_block_till_done()
    assert form["type"] is FlowResultType.FORM
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_discovery_empty_and_failure(hass) -> None:
    with patch(
        "custom_components.duosida_local.config_flow.discover_chargers",
        AsyncMock(return_value=()),
    ):
        empty = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "discover"})
    assert empty["reason"] == "no_devices_found"

    with patch(
        "custom_components.duosida_local.config_flow.discover_chargers",
        AsyncMock(side_effect=OSError),
    ):
        failed = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "discover"})
    assert failed["reason"] == "discovery_failed"


async def test_duplicate_updates_host(hass, identity) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=identity.device_id,
        data={CONF_HOST: "192.0.2.1", CONF_PORT: 9988},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.duosida_local.config_flow._async_probe",
        AsyncMock(return_value=identity),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "manual"}, data={CONF_HOST: "192.0.2.10", CONF_PORT: 9988}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_HOST] == "192.0.2.10"
    assert entry.data[CONF_ENERGY_OFFSET] == 0.0


async def test_reconfigure_success_and_different_device(hass, identity) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=identity.device_id,
        data={CONF_HOST: "192.0.2.1", CONF_PORT: 9988},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.duosida_local.config_flow._async_probe",
        AsyncMock(return_value=identity),
    ):
        form = await entry.start_reconfigure_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            form["flow_id"], {CONF_HOST: "192.0.2.20", CONF_PORT: 9988}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == "192.0.2.20"
    assert entry.data[CONF_ENERGY_OFFSET] == 0.0

    other = identity.__class__("1111111111111111111", "Other", "UCHEN", "FW")
    with patch(
        "custom_components.duosida_local.config_flow._async_probe",
        AsyncMock(return_value=other),
    ):
        flow = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
        )
        different = await hass.config_entries.flow.async_configure(
            flow["flow_id"], {CONF_HOST: "192.0.2.30", CONF_PORT: 9988}
        )
    assert different["errors"] == {"base": "different_device"}


async def test_reconfigure_connection_and_protocol_errors(hass, identity) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=identity.device_id,
        data={CONF_HOST: "192.0.2.1", CONF_PORT: 9988},
    )
    entry.add_to_hass(hass)
    for exception, expected in (
        (DuosidaConnectionError("offline"), "cannot_connect"),
        (DuosidaProtocolError("invalid"), "invalid_response"),
    ):
        with patch(
            "custom_components.duosida_local.config_flow._async_probe",
            AsyncMock(side_effect=exception),
        ):
            flow = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
            )
            result = await hass.config_entries.flow.async_configure(
                flow["flow_id"], {CONF_HOST: "192.0.2.30", CONF_PORT: 9988}
            )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": expected}


async def test_probe_always_disconnects(identity) -> None:
    client = AsyncMock()
    client.connect.return_value = identity
    with patch(
        "custom_components.duosida_local.config_flow.DuosidaClient", return_value=client
    ) as constructor:
        assert await _async_probe("192.0.2.10", 9988) == identity
    constructor.assert_called_once_with("192.0.2.10", 9988)
    client.disconnect.assert_awaited_once()


async def test_discovery_uses_enabled_adapter_broadcasts(hass) -> None:
    adapters = [
        {
            "enabled": True,
            "ipv4": [{"address": "192.0.2.10", "network_prefix": 24}],
        },
        {
            "enabled": False,
            "ipv4": [{"address": "198.51.100.10", "network_prefix": 24}],
        },
    ]
    discovery = AsyncMock(return_value=())
    with (
        patch(
            "custom_components.duosida_local.config_flow.network.async_get_adapters",
            AsyncMock(return_value=adapters),
        ),
        patch(
            "custom_components.duosida_local.config_flow.discover_chargers",
            discovery,
        ),
    ):
        assert await _async_discover_chargers(hass) == ()
    discovery.assert_awaited_once_with(
        timeout=4.0,
        additional_destinations=("192.0.2.255",),
    )
