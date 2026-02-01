from __future__ import annotations

from datetime import timedelta

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory

from .device import WBSmart
from .const import DOMAIN
# Устанавливает интервал с которым устройство будет опрашиваться
SCAN_INTERVAL = timedelta(seconds=5)
async def async_setup_entry(HomeAssistant, config_entry, async_add_entities):
    """Set up the switch platform."""
    import logging
    _LOGGER = logging.getLogger(__name__)
    
    device: WBSmart = HomeAssistant.data[DOMAIN][config_entry.entry_id]
    switches = []
    for i in range(6):
        switches.append(wb_switch(device, i))
        _LOGGER.info(f"📊 СОЗДАН {i} ПЕРЕКЛЮЧАТЕЛЬ")


    _LOGGER.info(f"📊 СОЗДАНО {len(switches)} ПЕРЕКЛЮЧАТЕЛЕЙ")
    async_add_entities(switches, update_before_add=False)


class wb_switch(SwitchEntity):
    def __init__(self, device: WBSmart, cannel: int):
        self._device = device
        self._attr_name = f"{device.get_name()}_{cannel+1}"
        self._attr_unique_id = self._attr_name
        self._cannel = cannel
        self._state = self._device.get_switch_status(self._cannel)
        #self._attr_entity_category = EntityCategory.CONFIG  # DIAGNOSTIC

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self._state = False
        await self._device.set_switch_status(self._cannel, self._state)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self._state = True
        await self._device.set_switch_status(self._cannel, self._state)

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        await self._device.update()
        self._state = self._device.get_switch_status(self._cannel)
        self._attr_available = self._device.is_connected()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.get_name())}
        }

    @property
    def is_on(self):
        """Check if Tuya switch is on."""
        return self._state
'''
    @property
    def icon(self):
        if self._device.get_switch_status(self._cannel):
            return "mdi:toggle-switch-variant"
        else:
            return "mdi:toggle-switch-variant-off"
'''