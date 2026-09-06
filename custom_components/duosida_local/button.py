"""Command buttons for Duosida Local."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from duosida_local import DuosidaError

from .entity import DuosidaEntity
from .runtime import DuosidaConfigEntry

PARALLEL_UPDATES = 1

BUTTONS = (
    ButtonEntityDescription(key="start", translation_key="start", icon="mdi:ev-station"),
    ButtonEntityDescription(key="stop", translation_key="stop", icon="mdi:stop-circle-outline"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DuosidaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up command buttons."""

    async_add_entities(DuosidaButton(entry, description) for description in BUTTONS)


class DuosidaButton(DuosidaEntity, ButtonEntity):
    """Execute a confirmed charger command."""

    entity_description: ButtonEntityDescription

    def __init__(self, entry: DuosidaConfigEntry, description: ButtonEntityDescription) -> None:
        super().__init__(entry, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        """Start or stop and surface failures to the service caller."""

        try:
            if self.entity_description.key == "start":
                await self.coordinator.client.start_charging()
            else:
                await self.coordinator.client.stop_charging()
        except DuosidaError as err:
            raise HomeAssistantError(
                translation_domain="duosida_local",
                translation_key="command_failed",
            ) from err
