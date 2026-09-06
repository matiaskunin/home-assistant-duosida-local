"""Redacted diagnostics for Duosida Local."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .runtime import DuosidaConfigEntry

TO_REDACT = {"host", "device_id", "serial", "mac", "identifiers", "unique_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: DuosidaConfigEntry
) -> dict[str, Any]:
    """Return state and identity with private identifiers removed."""

    runtime = entry.runtime_data
    payload: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "unique_id": entry.unique_id,
            "data": dict(entry.data),
        },
        "identity": asdict(runtime.identity),
        "status": asdict(runtime.coordinator.data) if runtime.coordinator.data else None,
        "connected": runtime.client.connected,
        "last_update_success": runtime.coordinator.last_update_success,
    }
    return async_redact_data(payload, TO_REDACT)
