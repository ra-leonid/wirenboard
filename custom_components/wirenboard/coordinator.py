from __future__ import annotations

from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)


_LOGGER = logging.getLogger(__name__)

class WBCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config_entry, device):

        super().__init__(
            hass,
            _LOGGER,
            name="Wirenboard coordinator",
            config_entry=config_entry,
            update_interval=timedelta(seconds=15),
            always_update=True
        )
        self.__device = device

    @property
    def device(self):
        return self.__device

    async def _async_setup(self):
        await self.__device.update()

    async def _async_update_data(self):
        await self.__device.update()
