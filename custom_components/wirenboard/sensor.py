from __future__ import annotations

import logging
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.sensor import  SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant

from .device import WBMr
from .const import DOMAIN
from .coordinator import WBCoordinator
from .entity import WbEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    objects = []
    coordinator: WBCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    device: WBMr = coordinator.device
    for obj in device.sensors:
        for i in range(obj.count):
            objects.append(EntryTriggerCounter(hass, coordinator, obj, i))

    _LOGGER.info(f"📊 СОЗДАНО {len(objects)} СЕНСОРОВ")
    async_add_entities(objects, update_before_add=False)


class EntryTriggerCounter(WbEntity, CoordinatorEntity, SensorEntity):
    def __init__(
            self,
            hass: HomeAssistant,
            coordinator: WBCoordinator,
            obj,
            idx: int
    ) -> None:
        _LOGGER.debug(f"select.py. ШАГ 1")
        super().__init__(hass, obj, idx)
        CoordinatorEntity.__init__(self, coordinator)

        #self._attr_device_class = SensorDeviceClass.BATTERY
        #self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        # self._attr_native_value = self._device.get_entry_trigger_count(self._channel)

    async def async_update(self) -> None:
        self._attr_native_value = self._device.get_entry_trigger_count(self._channel)

    @property
    def native_value(self):
        return self.object.get_state(self.id)

    @property
    def icon(self):
        return "mdi:counter"
