from __future__ import annotations
import logging

from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN
from homeassistant.core import (HomeAssistant, callback)
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

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
        self._attr_available = self.__device.is_connected
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        short_name = self.__device.name
        identifiers = {
            (DOMAIN, f"{short_name}-{self.__device.serial_number}")
        }
        name = f"{short_name}-{self.__device.device_id}",
        model = self.__device.model,
        sw_version = self.__device.firmware,
        manufacturer = self.__device.manufacturer

        _LOGGER.info(f"DeviceInfo(identifiers={identifiers}, name = {name}, model = {model}, "
                      f"sw_version = {sw_version}, manufacturer = {manufacturer}")

        return DeviceInfo(
            identifiers=identifiers,
            name = name,
            model = model,
            sw_version = sw_version,
            manufacturer = manufacturer
        )
