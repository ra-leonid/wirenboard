import logging

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .device import WBMr
from datetime import timedelta


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(HomeAssistant, config_entry, async_add_entities):

    device: WBMr = HomeAssistant.data[DOMAIN][config_entry.entry_id]

    selects = []
    for i in range(7):
        selects.append(wb_input_mode(device, i))
        _LOGGER.info(f"📊 СОЗДАН {i} выбор")

    selects.append(status_outputs_when_power_applied(device))

    _LOGGER.info(f"📊 СОЗДАНО {len(selects)} полей выбора")
    async_add_entities(selects, update_before_add=False)

SCAN_INTERVAL = timedelta(seconds=15)
class wb_input_mode(SelectEntity):
    _attr_current_option: str | None = None
    _attr_entity_registry_enabled_default = True
    _attr_icon = "mdi:button-pointer"

    def __init__(self, device: WBMr, cannel: int):
        self._attr_name = f"Режим работы входа {cannel}"
        # self._attr_unique_id = self._attr_name
        self._attr_unique_id = f"{device.name}_select_{cannel}"
        self.entity_id = f"{device.name}.select.{cannel}"
        self._attr_available = True
        self._attr_entity_category = EntityCategory.CONFIG  # DIAGNOSTIC

        self._device = device
        self._cannel = cannel

        self._attr_options = self._device.get_attr_options("input_mode", self._cannel)
        self.current_option = self.get_current_option()

    async def async_update(self):
        self.current_option = self.get_current_option()
        self._attr_available = self._device.is_connected

    async def async_select_option(self, option: str) -> None:
        await self._device.set_input_mode(self._cannel, option)

    def get_current_option(self):
        return self._device.get_switch_input_mode(self._cannel)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.name)}
        }


class status_outputs_when_power_applied(SelectEntity):
    _attr_current_option: str | None = None
    _attr_entity_registry_enabled_default = True
    _attr_icon = "mdi:list-status"

    def __init__(self, device: WBMr):
        self._attr_name = f"Состояния выходов при подаче питания"
        # self._attr_unique_id = self._attr_name
        self._attr_unique_id = f"{device.name}_select_status_outputs_when_power_applied"
        self.entity_id = f"{device.name}.select.status_outputs_when_power_applied"
        self._attr_available = True
        self._attr_entity_category = EntityCategory.CONFIG  # DIAGNOSTIC

        self._device = device

        self._attr_options = self._device.get_attr_options("status_outputs_when_power_applied")
        self.current_option = self.get_current_option()

    async def async_update(self):
        self.current_option = self.get_current_option()
        self._attr_available = self._device.is_connected

    async def async_select_option(self, option: str) -> None:
        await self._device.set_status_outputs_when_power_applied(option)

    def get_current_option(self):
        return self._device.get_status_outputs_when_power_applied()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.name)}
        }
