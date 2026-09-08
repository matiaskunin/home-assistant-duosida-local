"""Config flow for Duosida Local."""

from __future__ import annotations

from ipaddress import ip_interface
from typing import Any

import voluptuous as vol
from homeassistant.components import network
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from duosida_local import (
    ChargerIdentity,
    DiscoveredCharger,
    DuosidaClient,
    DuosidaConnectionError,
    DuosidaError,
    discover_chargers,
)

from .const import CONF_ENERGY_OFFSET, DEFAULT_ENERGY_OFFSET, DEFAULT_PORT, DOMAIN


class DuosidaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle discovery, manual setup and reconfiguration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Offer LAN discovery or manual setup."""

        return self.async_show_menu(step_id="user", menu_options=["discover", "manual"])

    async def async_step_discover(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Discover chargers when the user opens the discovery step."""

        if user_input is not None:
            host = user_input[CONF_HOST]
            return await self._async_validate_and_create(host, DEFAULT_PORT, DEFAULT_ENERGY_OFFSET)

        try:
            devices = await _async_discover_chargers(self.hass)
        except OSError:
            return self.async_abort(reason="discovery_failed")
        choices = {
            device.host: f"{device.host} ({device.device_id or 'unidentified'})"
            for device in devices
        }
        if not choices:
            return self.async_abort(reason="no_devices_found")
        return self.async_show_form(
            step_id="discover",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(value=host, label=label)
                                for host, label in choices.items()
                            ]
                        )
                    )
                }
            ),
        )

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Set up a charger by host."""

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                return await self._async_validate_and_create(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input.get(CONF_ENERGY_OFFSET, DEFAULT_ENERGY_OFFSET),
                )
            except DuosidaConnectionError:
                errors["base"] = "cannot_connect"
            except DuosidaError:
                errors["base"] = "invalid_response"
            except AbortFlow:
                raise
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): NumberSelector(
                        NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
                    ),
                    vol.Optional(CONF_ENERGY_OFFSET, default=DEFAULT_ENERGY_OFFSET): NumberSelector(
                        NumberSelectorConfig(
                            min=-1_000_000,
                            max=1_000_000,
                            step=0.001,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update host/port while retaining the stable device unique ID."""

        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                identity = await _async_probe(user_input[CONF_HOST], user_input[CONF_PORT])
                if identity.device_id != entry.unique_id:
                    errors["base"] = "different_device"
                else:
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            CONF_HOST: user_input[CONF_HOST],
                            CONF_PORT: user_input[CONF_PORT],
                            CONF_ENERGY_OFFSET: user_input.get(
                                CONF_ENERGY_OFFSET, DEFAULT_ENERGY_OFFSET
                            ),
                        },
                    )
            except DuosidaConnectionError:
                errors["base"] = "cannot_connect"
            except DuosidaError:
                errors["base"] = "invalid_response"

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=entry.data[CONF_HOST]): str,
                    vol.Required(
                        CONF_PORT, default=entry.data.get(CONF_PORT, DEFAULT_PORT)
                    ): NumberSelector(
                        NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
                    ),
                    vol.Optional(
                        CONF_ENERGY_OFFSET,
                        default=entry.data.get(CONF_ENERGY_OFFSET, DEFAULT_ENERGY_OFFSET),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=-1_000_000,
                            max=1_000_000,
                            step=0.001,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def _async_validate_and_create(
        self, host: str, port: int, energy_offset: float
    ) -> ConfigFlowResult:
        identity = await _async_probe(host, port)
        await self.async_set_unique_id(identity.device_id)
        self._abort_if_unique_id_configured(
            updates={
                CONF_HOST: host,
                CONF_PORT: port,
                CONF_ENERGY_OFFSET: energy_offset,
            }
        )
        return self.async_create_entry(
            title=f"Duosida {identity.model}",
            data={
                CONF_HOST: host,
                CONF_PORT: port,
                CONF_ENERGY_OFFSET: energy_offset,
            },
        )


async def _async_probe(host: str, port: int) -> ChargerIdentity:
    client = DuosidaClient(host, port)
    try:
        return await client.connect()
    finally:
        await client.disconnect()


async def _async_discover_chargers(hass: HomeAssistant) -> tuple[DiscoveredCharger, ...]:
    """Discover using global and adapter-specific IPv4 broadcasts."""

    broadcasts: set[str] = set()
    for adapter in await network.async_get_adapters(hass):
        if not adapter["enabled"]:
            continue
        for ipv4 in adapter["ipv4"]:
            interface = ip_interface(f"{ipv4['address']}/{ipv4['network_prefix']}")
            broadcasts.add(str(interface.network.broadcast_address))
    broadcasts.discard("255.255.255.255")
    return await discover_chargers(
        timeout=4.0,
        additional_destinations=tuple(sorted(broadcasts)),
    )
