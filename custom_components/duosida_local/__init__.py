"""Duosida Local integration setup."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from duosida_local import DuosidaClient, DuosidaError

from .const import CONF_HOST, CONF_PORT, DEFAULT_PORT
from .coordinator import DuosidaCoordinator
from .runtime import DuosidaConfigEntry, DuosidaRuntimeData

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: DuosidaConfigEntry) -> bool:
    """Set up Duosida Local from a config entry."""

    client = DuosidaClient(
        entry.data[CONF_HOST],
        entry.data.get(CONF_PORT, DEFAULT_PORT),
    )
    try:
        identity = await client.connect()
    except DuosidaError as err:
        await client.disconnect()
        raise ConfigEntryNotReady(str(err)) from err
    coordinator = DuosidaCoordinator(hass, entry, client)
    entry.runtime_data = DuosidaRuntimeData(client, coordinator, identity)
    await coordinator.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DuosidaConfigEntry) -> bool:
    """Unload platforms and network resources."""

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.coordinator.async_shutdown()
    return unloaded


async def _async_reload_entry(hass: HomeAssistant, entry: DuosidaConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
