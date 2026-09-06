"""Constants for Duosida Local."""

from typing import Final

DOMAIN: Final = "duosida_local"
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
DEFAULT_PORT: Final = 9988
MANUFACTURER: Final = "DUOSIDA"
ATTR_COMMAND_STATUS: Final = "command_status"

PLATFORMS: Final = ["sensor", "binary_sensor", "button", "number"]
