"""Binary sensors for Duosida Local."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from duosida_local import ChargerStatus

from .entity import DuosidaEntity
from .runtime import DuosidaConfigEntry


@dataclass(frozen=True, kw_only=True)
class DuosidaBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a binary charger state."""

    value_fn: Callable[[ChargerStatus], bool]


BINARY_SENSORS = (
    DuosidaBinarySensorDescription(
        key="vehicle_connected",
        translation_key="vehicle_connected",
        device_class=BinarySensorDeviceClass.PLUG,
        value_fn=lambda status: status.vehicle_connected,
    ),
    DuosidaBinarySensorDescription(
        key="charging",
        translation_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda status: status.charging,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DuosidaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensors."""

    async_add_entities(DuosidaBinarySensor(entry, description) for description in BINARY_SENSORS)


class DuosidaBinarySensor(DuosidaEntity, BinarySensorEntity):
    """Read a boolean from the coordinator snapshot."""

    entity_description: DuosidaBinarySensorDescription

    def __init__(
        self, entry: DuosidaConfigEntry, description: DuosidaBinarySensorDescription
    ) -> None:
        super().__init__(entry, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the latest boolean without I/O."""

        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
