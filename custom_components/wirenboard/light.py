from __future__ import annotations

import logging
import math

from homeassistant.components.light import (ATTR_BRIGHTNESS, ColorMode, LightEntity)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.color import brightness_to_value, value_to_brightness

from .device import Platform
from .const import DOMAIN
from .coordinator import WBCoordinator
from .entity import WbEntity


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator: WBCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    await coordinator.async_add_device_entities(Platform.light, WbLight, async_add_entities)


class WbLight(WbEntity, CoordinatorEntity, LightEntity):
    def __init__(
        self, 
        hass: HomeAssistant, 
        coordinator: WBCoordinator,
            **kwargs
    ) -> None:
        super().__init__(hass, **kwargs)
        CoordinatorEntity.__init__(self, coordinator)

        addresses = kwargs["addresses"]


        brightness = addresses.get("brightness")

        if brightness is None:
            self._attr_color_mode = ColorMode.ONOFF
            self._attr_supported_color_modes = {ColorMode.ONOFF}
        else:
            self.supported_brightness = True
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
            self.__brightness_address = brightness["address"]
            self.__brightness_type = brightness["type"]
            self.__brightness_field_format = brightness["field_format"]
            self.__brightness_type = brightness["type"]
            self.__field_format = brightness["field_format"]
            if "min_val" in brightness or "max_val" in brightness:
                self.__brightness_scale = (brightness.get("min_val", 0), brightness.get("max_val", 0))
            else:
                self.__brightness_scale = None

    @property
    def is_on(self) -> bool:
        return self.object.get_state(self.id, "base")

    @property
    def brightness(self) -> int:
        value = self.object.get_state(self.id, "brightness")

        if self.__brightness_scale is not None:
            return value_to_brightness(self.__brightness_scale, value)

        return value

    async def async_turn_on(self, **kwargs) -> None:
        if ATTR_BRIGHTNESS in kwargs:
            if self.__brightness_scale is None:
                brightness = kwargs[ATTR_BRIGHTNESS]
            else:
                brightness = math.ceil(brightness_to_value(self.__brightness_scale, kwargs[ATTR_BRIGHTNESS]))

            await self.set_value(
                "brightness",
                self.__brightness_address,
                self.__brightness_type,
                self.__brightness_field_format,
                brightness)
        else:
            await self.set_value("base", self.address, self.register_type, self.field_format, True)

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.set_value("base", self.address, self.register_type, self.field_format, False)
        self.async_write_ha_state()
