"""Config flow for Duosida Local."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
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
    DuosidaClient,
    DuosidaConnectionError,
    DuosidaError,
    discover_chargers,
)

from .const import DEFAULT_PORT, DOMAIN


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
            return await self._async_validate_and_create(host, DEFAULT_PORT)

        try:
            devices = await discover_chargers(timeout=3.0)
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
                    user_input[CONF_HOST], user_input[CONF_PORT]
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
                }
            ),
            errors=errors,
        )

    async def _async_validate_and_create(self, host: str, port: int) -> ConfigFlowResult:
        identity = await _async_probe(host, port)
        await self.async_set_unique_id(identity.device_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})
        return self.async_create_entry(
            title=f"Duosida {identity.model}",
            data={CONF_HOST: host, CONF_PORT: port},
        )


async def _async_probe(host: str, port: int) -> ChargerIdentity:
    client = DuosidaClient(host, port)
    try:
        return await client.connect()
    finally:
        await client.disconnect()
