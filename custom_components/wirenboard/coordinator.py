from __future__ import annotations

from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from .device import WBMr


_LOGGER = logging.getLogger(__name__)

class WBCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    # def __init__(self, hass, config_entry, my_api):
    def __init__(self, hass, config_entry, device):

        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="My coordinator",
            config_entry=config_entry,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=1),
            # Set always_update to `False` if the data returned from the
            # api can be compared via `__eq__` to avoid duplicate updates
            # being dispatched to listeners
            always_update=True
        )
        self._device = device

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        # self._device = await self.my_api.get_device()
        await self._device.update()
        await self._device.update_setting()


    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        # try:
        #     # Note: asyncio.TimeoutError and aiohttp.ClientError are already
        #     # handled by the data update coordinator.
        #     async with async_timeout.timeout(10):
        #         # Grab active context variables to limit data required to be fetched from API
        #         # Note: using context is not required if there is no need or ability to limit
        #         # data retrieved from API.
        #         listening_idx = set(self.async_contexts())
        #         return await self.my_api.fetch_data(listening_idx)
        # except ApiAuthError as err:
        #     # Raising ConfigEntryAuthFailed will cancel future updates
        #     # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        #     raise ConfigEntryAuthFailed from err
        # except ApiError as err:
        #     raise UpdateFailed(f"Error communicating with API: {err}")
        # except ApiRateLimited as err:
        #     # If the API is providing backoff signals, these can be honored via the retry_after parameter
        #     raise UpdateFailed(retry_after=60)

        await self._device.update()
