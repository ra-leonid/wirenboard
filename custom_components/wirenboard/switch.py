from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .device import Platform
from .const import DOMAIN
from .coordinator import WBCoordinator
from .entity import WbEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator: WBCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    await coordinator.async_add_device_entities(Platform.switch, WbSwitch, async_add_entities)

class WbSwitch(WbEntity, CoordinatorEntity, SwitchEntity):
    def __init__(
            self,
            hass: HomeAssistant,
            coordinator: WBCoordinator,
            **kwargs
    ) -> None:
        _LOGGER.debug(f"switch.py. ШАГ 1")
        super().__init__(hass, **kwargs)
        CoordinatorEntity.__init__(self, coordinator)
        _LOGGER.debug(f"switch.py. ШАГ 2")

    @property
    def is_on(self) -> bool:
        return self.object.get_state(self.id)

    async def async_turn_off(self, **kwargs):
        await self.set_value("base", False)
        # self.async_write_ha_state()


    async def async_turn_on(self, **kwargs):
        await self.set_value("base", True)
        # self.async_write_ha_state()
