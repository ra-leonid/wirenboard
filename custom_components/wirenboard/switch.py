from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
# from homeassistant.core import (HomeAssistant, callback)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .device import WBMr
from .const import DOMAIN
from .coordinator import WBCoordinator
from .entity import WbEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    objects = []
    coordinator: WBCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    device: WBMr = coordinator.device
    for obj in device.switches:
        for i in range(obj.count):
            objects.append(WbSwitch(hass, coordinator, obj, i))

    _LOGGER.info(f"📊 СОЗДАНО {len(objects)} ПЕРЕКЛЮЧАТЕЛЕЙ")
    async_add_entities(objects, update_before_add=False)

class WbSwitch(WbEntity, CoordinatorEntity, SwitchEntity):
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

    @property
    def is_on(self) -> bool:
        return self.object.get_state(self.id)

    async def async_turn_off(self, **kwargs):
        await self.object.set_value(self.id, False)
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        await self.object.set_value(self.id, True)
        self.async_write_ha_state()
