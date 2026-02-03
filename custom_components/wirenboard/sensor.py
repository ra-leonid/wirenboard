
'''from __future__ import annotations

from collections import namedtuple
from datetime import timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (UnitOfVolume,PERCENTAGE)
from .const import DOMAIN
from .device import NeptunSmart, WirelessSensor, Counter
'''

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from .device import WBMr
from .const import DOMAIN


# Устанавливает интервал с которым устройство будет опрашиваться
SCAN_INTERVAL = timedelta(seconds=1)
async def async_setup_entry(HomeAssistant, config_entry, async_add_entities):
    device: WBMr = HomeAssistant.data[DOMAIN][config_entry.entry_id]
    sensors = []

    # Счетчик срабатываний входа
    for i in range(device.input_count):
        sensors.append(EntryTriggerCounter(device, i))

    async_add_entities(sensors, update_before_add=False)

class EntryTriggerCounter(SensorEntity):
    def __init__(self, device: WBMr, channel: int):
        self._device = device
        self._channel = channel

        self._attr_unique_id = f"{device.name}_count_sensor_{self._channel}"
        self._attr_name = f"Счетчик срабатываний входа {self._channel} канал"
        #self._attr_device_class = SensorDeviceClass.BATTERY
        #self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = self._device.get_entry_trigger_count(self._channel)

    async def async_update(self) -> None:
        self._attr_native_value = self._device.get_entry_trigger_count(self._channel)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.name)}
        }

    @property
    def icon(self):
        return "mdi:counter"
