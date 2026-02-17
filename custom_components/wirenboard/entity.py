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
        self.__id = kwargs["id"]

        # self.__addresses = kwargs["addresses"]
        addresses = kwargs["addresses"]
        self.__address = addresses["base"]["address"]
        self.__register_type = addresses["base"]["type"]
        self.__field_format = addresses["base"]["field_format"]

        channel = kwargs.get('channel', "")

        if channel == "":
            prefix_channel = ""
        else:
            prefix_channel = f"_{channel}"

        unique_id = f"{self.__device_info["name"]}_{self.__device_info["serial_number"]}_{kwargs["object_name_id"]}{prefix_channel}"
        name = f"{kwargs["object_name"]} {channel}".strip()

        # _LOGGER.info(f"unique_id={unique_id}, name = {name}")

        self._attr_unique_id = unique_id
        self._attr_name = name
        # self.entity_id = f"{kwargs["platform_name"]}.{DOMAIN.lower()}_{self._attr_unique_id}"

        entity_category = kwargs["entity_category"]
        if entity_category is not None:
            self._attr_entity_category = entity_category


    # @property
    # def addresses(self):
    #     return self.__addresses

    @property
    def address(self):
        return self.__address

    @property
    def register_type(self):
        return self.__register_type

    @property
    def field_format(self):
        return self.__field_format

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
        # _LOGGER.info(f"DeviceInfo(identifiers={identifiers}, name = {self.__device_info["name"]}, model = {self.__device_info["model"]}, "
        #     f"sw_version = {self.__device_info["sw_version"]}, manufacturer = {self.__device_info["manufacturer"]}")

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

    async def set_value(self, value_name, address, register_type, field_format, value) -> None:
        # await self.object.set_value(self.addresses, self.id, value_name, value)
        await self.object.set_value_new(address, register_type, self.id, value_name, field_format, value)
        self._attr_available = self.__device.connected
