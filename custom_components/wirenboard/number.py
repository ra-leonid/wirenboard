from __future__ import annotations

import logging
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.number import  NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant

from .device import WBMr, Platform
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
    objects = []
    coordinator: WBCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    device: WBMr = coordinator.device

    for obj in device.filtre_objects(Platform.number):
        for i in range(obj.count):
            objects.append(WbNumber(hass, coordinator, obj, i))

    _LOGGER.info(f"📊 СОЗДАНО {len(objects)} ЧИСЛОВЫХ ПОЛЕЙ ВВОДА")
    async_add_entities(objects, update_before_add=False)


class WbNumber(WbEntity, CoordinatorEntity, NumberEntity):
    def __init__(
            self,
            hass: HomeAssistant,
            coordinator: WBCoordinator,
            obj,
            idx: int
    ) -> None:
        _LOGGER.debug(f"number.py. ШАГ 1")
        super().__init__(hass, obj, idx)
        CoordinatorEntity.__init__(self, coordinator)

        self._data_type = "int16"
        self.native_min_value = obj.min_val
        self.native_max_value = obj.max_val
        self.mode = obj.mode
        self.native_step = obj.step
        self._scale = obj.scale

    async def async_update(self) -> None:
        self._attr_native_value = self._device.get_entry_trigger_count(self._channel)

    @property
    def native_value(self):
        return self.object.get_state(self.id)

    async def async_set_native_value(self, value) -> None:
        if self._data_type == "int16":
            _value = int(value)
        else:
            _value = float(value)
        await self.object.set_value(self.id, _value)

    #
    # @property
    # def icon(self):
    #     return "mdi:counter"
