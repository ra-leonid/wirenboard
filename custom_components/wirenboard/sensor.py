from __future__ import annotations

import logging
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.sensor import  SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant

from .device import Platform
from .const import DOMAIN
from .coordinator import WBCoordinator
from .entity import WbEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator: WBCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    await coordinator.async_add_device_entities(Platform.sensor, EntryTriggerCounter, async_add_entities)


class EntryTriggerCounter(WbEntity, CoordinatorEntity, SensorEntity):
    def __init__(
            self,
            hass: HomeAssistant,
            coordinator: WBCoordinator,
            **kwargs
    ) -> None:
        super().__init__(hass, **kwargs)
        _LOGGER.debug(f"select.py. ШАГ 1")
        CoordinatorEntity.__init__(self, coordinator)

        #self._attr_device_class = SensorDeviceClass.BATTERY
        #self._attr_native_unit_of_measurement = PERCENTAGE
        # self._attr_entity_category = EntityCategory.DIAGNOSTIC
        # self._attr_native_value = self._device.get_entry_trigger_count(self._channel)

    async def async_update(self) -> None:
        self._attr_native_value = self.object.get_state(self.id)

    @property
    def native_value(self):
        return self.object.get_state(self.id)

    @property
    def icon(self):
        return "mdi:counter"