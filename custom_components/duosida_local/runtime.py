"""Runtime types shared by the integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry

from duosida_local import ChargerIdentity, DuosidaClient

from .coordinator import DuosidaCoordinator


@dataclass(slots=True)
class DuosidaRuntimeData:
    """Objects owned by one config entry."""

    client: DuosidaClient
    coordinator: DuosidaCoordinator
    identity: ChargerIdentity


type DuosidaConfigEntry = ConfigEntry[DuosidaRuntimeData]
