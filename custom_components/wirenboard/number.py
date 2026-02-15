from __future__ import annotations

import logging
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.number import  NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant

from .device import Platform
from .const import DOMAIN
from .coordinator import WBCoordinator
from .entity import WbEntity

_LOGGER = logging.getLogger(__name__)
# DATA_TYPE_MAP = {
#     "uint16": "H",
#     "int16": "h",
#     "uint32": "I",
#     "int32": "i",
#     "float32": "f",
# }


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator: WBCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    await coordinator.async_add_device_entities(Platform.number, WbNumber, async_add_entities)

class WbNumber(WbEntity, CoordinatorEntity, NumberEntity):
    def __init__(
            self,
            hass: HomeAssistant,
            coordinator: WBCoordinator,
            **kwargs
    ) -> None:
        super().__init__(hass, **kwargs)
        _LOGGER.debug(f"number.py. ШАГ 1")
        CoordinatorEntity.__init__(self, coordinator)

        self.native_min_value = kwargs["min_val"]
        self.native_max_value = kwargs["max_val"]
        self.mode = kwargs["mode"]
        self.native_step = kwargs["step"]
        self._scale = kwargs["scale"]

    async def async_update(self) -> None:
        self._attr_native_value = self.object.get_state(self.id)

    @property
    def native_value(self):
        return self.object.get_state(self.id)

    async def async_set_native_value(self, value) -> None:
        await self.set_value("base", value)
        #self.async_write_ha_state()

    #
    # @property
    # def icon(self):
    #     return "mdi:counter"
