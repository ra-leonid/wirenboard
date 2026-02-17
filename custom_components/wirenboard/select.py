import logging
from typing import Any
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant

from .device import Platform
from .const import DOMAIN
from .coordinator import WBCoordinator
from .entity import WbEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator: WBCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    await coordinator.async_add_device_entities(Platform.select, WbSelect, async_add_entities)

class WbSelect(WbEntity, CoordinatorEntity, SelectEntity):
    _attr_current_option: str | None = None
    _attr_entity_registry_enabled_default = True
    _attr_icon = "mdi:list-status"
    def __init__(
            self,
            hass: HomeAssistant,
            coordinator: WBCoordinator,
            **kwargs
    ) -> None:
        super().__init__(hass, **kwargs)
        CoordinatorEntity.__init__(self, coordinator)

        self.__select_values = kwargs["addresses"]["base"]["select_values"]
        self._attr_options = list(self.__select_values.values())
        self.current_option = self.get_current_option()

    async def async_select_option(self, option: str) -> None:
        # Возвращает первый найденный ключ
        value = next((k for k, v in self.__select_values.items() if v == option), None)
        await self.set_value("base", self.address, self.register_type, self.field_format, value)
        self.current_option = self.get_current_option()
        self.async_write_ha_state()

    def get_current_option(self):
        key = self.object.get_state(self.id, "base")
        return self.__select_values[key]