"""Sensor entities for Duosida Local."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from duosida_local import ChargerIdentity, ChargerStatus

from .entity import DuosidaEntity
from .runtime import DuosidaConfigEntry


@dataclass(frozen=True, kw_only=True)
class DuosidaSensorDescription(SensorEntityDescription):
    """Describe a status-backed sensor."""

    value_fn: Callable[[ChargerStatus], str | int | float]


@dataclass(frozen=True, kw_only=True)
class DuosidaIdentitySensorDescription(SensorEntityDescription):
    """Describe an identity-backed diagnostic sensor."""

    value_fn: Callable[[ChargerIdentity], str]


SENSORS: tuple[DuosidaSensorDescription, ...] = (
    DuosidaSensorDescription(
        key="state", translation_key="state", value_fn=lambda status: status.state.value
    ),
    DuosidaSensorDescription(
        key="voltage",
        translation_key="voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda status: status.voltage,
    ),
    DuosidaSensorDescription(
        key="current",
        translation_key="current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda status: status.current,
    ),
    DuosidaSensorDescription(
        key="power",
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda status: status.power,
    ),
    DuosidaSensorDescription(
        key="total_energy",
        translation_key="total_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=3,
        value_fn=lambda status: status.total_energy,
    ),
    DuosidaSensorDescription(
        key="session_energy",
        translation_key="session_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=3,
        value_fn=lambda status: status.session_energy,
    ),
    DuosidaSensorDescription(
        key="station_temperature",
        translation_key="station_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda status: status.station_temperature,
    ),
    DuosidaSensorDescription(
        key="cp_voltage",
        translation_key="cp_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        suggested_display_precision=2,
        value_fn=lambda status: status.cp_voltage,
    ),
    DuosidaSensorDescription(
        key="raw_state",
        translation_key="raw_state",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda status: status.raw_state,
    ),
)

IDENTITY_SENSORS: tuple[DuosidaIdentitySensorDescription, ...] = (
    DuosidaIdentitySensorDescription(
        key="device_id",
        translation_key="device_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda identity: identity.device_id,
    ),
    DuosidaIdentitySensorDescription(
        key="model",
        translation_key="model",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda identity: identity.model,
    ),
    DuosidaIdentitySensorDescription(
        key="manufacturer",
        translation_key="manufacturer",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda identity: identity.manufacturer,
    ),
    DuosidaIdentitySensorDescription(
        key="firmware",
        translation_key="firmware",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda identity: identity.firmware,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DuosidaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up status sensors."""

    async_add_entities(
        [
            *(DuosidaSensor(entry, description) for description in SENSORS),
            *(DuosidaIdentitySensor(entry, description) for description in IDENTITY_SENSORS),
        ]
    )


class DuosidaSensor(DuosidaEntity, SensorEntity):
    """Read a value from the coordinator snapshot."""

    entity_description: DuosidaSensorDescription

    def __init__(self, entry: DuosidaConfigEntry, description: DuosidaSensorDescription) -> None:
        super().__init__(entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> str | int | float | None:
        """Return the latest value without I/O."""

        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)


class DuosidaIdentitySensor(DuosidaEntity, SensorEntity):
    """Expose static technical information without network I/O."""

    entity_description: DuosidaIdentitySensorDescription

    def __init__(
        self, entry: DuosidaConfigEntry, description: DuosidaIdentitySensorDescription
    ) -> None:
        super().__init__(entry, description.key)
        self.entity_description = description
        self._identity = entry.runtime_data.identity

    @property
    def native_value(self) -> str:
        """Return the immutable identity value."""

        return self.entity_description.value_fn(self._identity)
