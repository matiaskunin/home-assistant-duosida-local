"""Base entity for Duosida Local."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DuosidaCoordinator
from .runtime import DuosidaConfigEntry


class DuosidaEntity(CoordinatorEntity[DuosidaCoordinator]):
    """Entity sharing one push coordinator."""

    _attr_has_entity_name = True

    def __init__(self, entry: DuosidaConfigEntry, key: str) -> None:
        super().__init__(entry.runtime_data.coordinator)
        identity = entry.runtime_data.identity
        self._attr_unique_id = f"{identity.device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identity.device_id)},
            manufacturer=identity.manufacturer,
            model=identity.model,
            sw_version=identity.firmware,
            name="Duosida EV charger",
        )
