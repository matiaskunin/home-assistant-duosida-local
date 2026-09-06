"""Push coordinator with bounded exponential reconnection."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from duosida_local import ChargerStatus, DuosidaClient, DuosidaError

_LOGGER = logging.getLogger(__name__)
_BACKOFF_SECONDS = (1, 2, 5, 10, 30, 60)


class DuosidaCoordinator(DataUpdateCoordinator[ChargerStatus]):
    """Translate the library state stream into Home Assistant updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry[Any], client: DuosidaClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="Duosida Local",
            update_interval=None,
        )
        self._entry = entry
        self.client = client
        self._stream_task: asyncio.Task[None] | None = None
        self._stopping = False

    async def _async_update_data(self) -> ChargerStatus:
        """Connect and obtain the initial status for first refresh/recovery."""

        try:
            await self.client.connect()
            async with asyncio.timeout(15):
                async for status in self.client.states():
                    return status
        except (TimeoutError, DuosidaError) as err:
            raise UpdateFailed(str(err)) from err
        raise UpdateFailed("charger state stream ended")

    async def async_start(self) -> None:
        """Perform first refresh and start consuming push updates."""

        await self.async_config_entry_first_refresh()
        self._stream_task = self._entry.async_create_background_task(
            self.hass,
            self._async_stream_with_reconnect(),
            "duosida-local-state-stream",
        )

    async def async_shutdown(self) -> None:
        """Stop reconnect attempts and close the client."""

        self._stopping = True
        task, self._stream_task = self._stream_task, None
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        await self.client.disconnect()

    async def _async_stream_with_reconnect(self) -> None:
        attempt = 0
        while not self._stopping:
            try:
                async for status in self.client.states():
                    attempt = 0
                    self.async_set_updated_data(status)
                raise UpdateFailed("charger state stream ended")
            except asyncio.CancelledError:
                raise
            except (DuosidaError, UpdateFailed) as err:
                self.async_set_update_error(err)
                await self.client.disconnect()
                delay = _BACKOFF_SECONDS[min(attempt, len(_BACKOFF_SECONDS) - 1)]
                attempt += 1
                if attempt == 5:
                    ir.async_create_issue(
                        self.hass,
                        "duosida_local",
                        f"connection_lost_{self._entry.entry_id}",
                        is_fixable=False,
                        severity=ir.IssueSeverity.WARNING,
                        translation_key="connection_lost",
                        translation_placeholders={"host": self.client.host},
                    )
                _LOGGER.debug("Reconnecting to Duosida charger in %s seconds", delay)
                await asyncio.sleep(delay)
                try:
                    status = await self._async_update_data()
                except UpdateFailed:
                    continue
                ir.async_delete_issue(
                    self.hass,
                    "duosida_local",
                    f"connection_lost_{self._entry.entry_id}",
                )
                self.async_set_updated_data(status)
