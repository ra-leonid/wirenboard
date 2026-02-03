from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components.switch import SwitchEntity

from .device import WBMr
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


# Устанавливает интервал с которым устройство будет опрашиваться
SCAN_INTERVAL = timedelta(seconds=5)
async def async_setup_entry(HomeAssistant, config_entry, async_add_entities):
    device: WBMr = HomeAssistant.data[DOMAIN][config_entry.entry_id]
    switches = []

    for i in range(device.relay_count):
        switches.append(wb_switch(device, i))
        _LOGGER.info(f"📊 СОЗДАН {i} ПЕРЕКЛЮЧАТЕЛЬ")

    _LOGGER.info(f"📊 СОЗДАНО {len(switches)} ПЕРЕКЛЮЧАТЕЛЕЙ")
    async_add_entities(switches, update_before_add=False)


class wb_switch(SwitchEntity):
    def __init__(self, device: WBMr, channel: int):
        self._attr_has_entity_name = True
        self._attr_name = f"Реле {channel+1}"
        self._device = device
        #self._attr_unique_id = self._attr_name
        self._attr_unique_id = f"{device.name}_switch_{channel+1}"
        self._channel = channel
        self._attr_is_on = self._device.get_switch_status(self._channel)
        #self._attr_entity_category = EntityCategory.CONFIG  # DIAGNOSTIC

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self._attr_is_on = False
        await self._device.set_switch_status(self._channel, self._attr_is_on)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self._attr_is_on = True
        await self._device.set_switch_status(self._channel, self._attr_is_on)

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        await self._device.update()
        self._attr_is_on = self._device.get_switch_status(self._channel)
        self._attr_available = self._device.is_connected

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.name)}
        }

    '''
    @property
    def icon(self):
        if self._device.get_switch_status(self._channel):
            return "mdi:toggle-switch-variant"
        else:
            return "mdi:toggle-switch-variant-off"
'''
