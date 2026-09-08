"""Constants for Duosida Local."""

from typing import Final

DOMAIN: Final = "duosida_local"
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_ENERGY_OFFSET: Final = "energy_offset"
DEFAULT_PORT: Final = 9988
DEFAULT_ENERGY_OFFSET: Final = 0.0
MANUFACTURER: Final = "DUOSIDA"
ATTR_COMMAND_STATUS: Final = "command_status"

PLATFORMS: Final = ["sensor", "binary_sensor", "button", "number"]
