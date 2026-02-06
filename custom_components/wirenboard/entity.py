from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN
from homeassistant.core import (HomeAssistant, callback)
from homeassistant.helpers.entity import Entity

class WbEntity(Entity):
    def __init__(self, hass: HomeAssistant, obj, idx: int | None) -> None:
        self._hass = hass
        self.__device = obj.device
        self.__object = obj
        self.__id = idx

        channel = obj.get_channel(idx)
        if channel is None:
            prefix_channel = ""
        else:
            prefix_channel = f"_{obj.name_id}_{channel}"

        self._attr_unique_id = f"{self.__device.name.lower()}{prefix_channel}"
        self.entity_id = f"{obj.platform.name}.{DOMAIN.lower()}_{self._attr_unique_id}"
        self._attr_name = f"{obj.name} {channel}".strip()

        if self.__object.entity_category is not None:
            self._attr_entity_category = self.__object.entity_category


    @property
    def object(self):
        return self.__object

    @property
    def id(self):
        return self.__id

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        short_name = self.__device.name
        return DeviceInfo(
            identifiers={
                (DOMAIN, f"{short_name}-{self.__device.device_id}")
            },
            name = f"{short_name}-{self.__device.device_id}",
            model = self.__device.model,
            sw_version = self.__device.firmware,
            manufacturer = self.__device.manufacturer
        )
    # TODO реализовать вывод информации об устройстве "https://selectel.ru/blog/ha-karadio/" def device_info



    #
    # @property
    # def name(self) -> str:
    #     """Return the display name of this light."""
    #     return self._name
    #
    #
    # @property
    # def unique_id(self) -> str:
    #     """Return the display name of this light."""
    #     return self._unique_id