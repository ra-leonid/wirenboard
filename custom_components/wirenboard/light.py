from __future__ import annotations

import logging
from homeassistant.components.light import (ATTR_BRIGHTNESS, ColorMode, LightEntity)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .device import Platform
from .const import DOMAIN
from .coordinator import WBCoordinator
from .entity import WbEntity


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator: WBCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    await coordinator.async_add_device_entities(Platform.switch, WbLight, async_add_entities)


class WbLight(WbEntity, CoordinatorEntity, LightEntity):
    def __init__(
        self, 
        hass: HomeAssistant, 
        coordinator: WBCoordinator,
            obj,
            idx: int
    ) -> None:
        _LOGGER.debug(f"switch.py. ШАГ 1")
        super().__init__(hass, obj, idx)
        CoordinatorEntity.__init__(self, coordinator)
        _LOGGER.debug(f"switch.py. ШАГ 2")

        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_color_mode = ColorMode.ONOFF

        if self.object.supported_brightness(self.id):
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)

    @property
    def is_on(self) -> bool:
        return self.object.get_state(self.id)

    @property
    def brightness(self) -> int:
        return self.object.get_brightness(self.id)

    async def async_turn_on(self, **kwargs) -> None:
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            await self.object.async_set_brightness(self.id, brightness)
        else:
            await self.set_value(True)
        # self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.set_value(False)
        # self.async_write_ha_state()
