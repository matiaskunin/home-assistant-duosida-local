"""Maximum-current number for Duosida Local."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from duosida_local import CommandReceipt, DuosidaError

from .const import ATTR_COMMAND_STATUS
from .entity import DuosidaEntity
from .runtime import DuosidaConfigEntry

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DuosidaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the write-only current limit."""

    async_add_entities([DuosidaMaxCurrent(entry)])


class DuosidaMaxCurrent(DuosidaEntity, NumberEntity):
    """Represent the current limit last requested through Home Assistant."""

    _attr_translation_key = "max_current"
    _attr_icon = "mdi:current-ac"
    _attr_device_class = NumberDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_native_min_value = 6
    _attr_native_max_value = 32
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_assumed_state = True

    def __init__(self, entry: DuosidaConfigEntry) -> None:
        super().__init__(entry, "max_current")
        self._attr_native_value = 6
        self._receipt: CommandReceipt | None = None

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Expose that the write-only value was not read back."""

        if self._receipt is None:
            return {}
        return {ATTR_COMMAND_STATUS: self._receipt.status.value}

    async def async_set_native_value(self, value: float) -> None:
        """Send an integer 6-32 A limit."""

        amps = int(value)
        if value != amps:
            raise HomeAssistantError(
                translation_domain="duosida_local", translation_key="whole_amps_required"
            )
        try:
            self._receipt = await self.coordinator.client.set_max_current(amps)
        except DuosidaError as err:
            raise HomeAssistantError(
                translation_domain="duosida_local", translation_key="command_failed"
            ) from err
        self._attr_native_value = amps
        self.async_write_ha_state()
