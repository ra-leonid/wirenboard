from __future__ import annotations
import logging

from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN
from homeassistant.core import (HomeAssistant, callback)
from homeassistant.helpers.entity import Entity

from .coordinator import WBCoordinator
_LOGGER = logging.getLogger(__name__)

class WbEntity(Entity):
    def __init__(self, hass: HomeAssistant, **kwargs) -> None:
        self._hass = hass
        self.__object = kwargs["object"]
        self.__device_info = kwargs["device_info"]
        self.__device = self.__device_info["device"]
        # addresses={"base":{"address":int,"type":RegisterType, "select_values":{...}}}, "brightness":{"address":int,"type":RegisterType}}
        self.__addresses = kwargs["addresses"]
        self.__id = kwargs["id"]

        channel = kwargs.get('channel', "")

        if channel == "":
            prefix_channel = ""
        else:
            prefix_channel = f"_{kwargs["object_name_id"]}_{channel}"

        self._attr_unique_id = f"{self.__device_info["name"]}_{self.__device_info["serial_number"]}{prefix_channel}"
        self.entity_id = f"{kwargs["platform_name"]}.{DOMAIN.lower()}_{self._attr_unique_id}"
        self._attr_name = f"{kwargs["object_name"]} {channel}".strip()

        # entity_category = kwargs["entity_category"]
        # if entity_category is not None:
        #     self._attr_entity_category = entity_category


    @property
    def addresses(self):
        return self.__addresses

    @property
    def id(self):
        return self.__id

    @property
    def object(self):
        return self.__object # TODO отказаться от __object

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_available = self.__device.connected #TODO отказаться от __device
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        identifiers = {
            (DOMAIN, f"{self.__device_info["name"]}_{self.__device_info["serial_number"]}")
        }
        _LOGGER.info(f"DeviceInfo(identifiers={identifiers}, name = {self.__device_info["name"]}, model = {self.__device_info["model"]}, "
            f"sw_version = {self.__device_info["sw_version"]}, manufacturer = {self.__device_info["manufacturer"]}")

        # TODO Рассмотреть возможность передачи через **kwargs
        return DeviceInfo(
            identifiers=identifiers,
            name = self.__device_info["name"],
            model = self.__device_info["model"],
            model_id = self.__device_info["device_id"],
            serial_number = self.__device_info["serial_number"],
            sw_version = self.__device_info["sw_version"],
            manufacturer = self.__device_info["manufacturer"]
        )

    async def set_value(self, value_name, value) -> None:
        await self.object.set_value(self.addresses, self.id, value_name, value)
        self._attr_available = self.__device.connected
        self.async_write_ha_state()
