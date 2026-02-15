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
#
# async def async_setup_entry(hass, config_entry, async_add_entities):
#     objects1 = []
#     coordinator: WBCoordinator = hass.data[DOMAIN][config_entry.entry_id]
#     for device in coordinator.devices:
#         for objects in device.get_objects(Platform.select):
#             index = 0
#             for address_group in objects.addresses_group:
#                 index, components_values = objects.get_component_values(address_group, index)
#                 for values in components_values:
#                     _LOGGER.info(f"async_setup_entry. values={values}")
#                     objects1.append(WbSelect(coordinator.hass, coordinator, **values))
#
#     _LOGGER.info(f"📊 СОЗДАНО {len(objects1)} ПОЛЕЙ ВЫБОРА")
#     async_add_entities(objects1, update_before_add=False)


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

        # self._attr_has_entity_name = True # Этого реквизита нет в классе WbEntity
        # self._attr_available = True # Этого реквизита нет в классе WbEntity
        _LOGGER.info(f"__init__. self.addresses={self.addresses}")

        self._attr_options = self.addresses["base"]["select_values"]
        self.current_option = self.get_current_option()
        _LOGGER.info(f"__init__. self._attr_options={self._attr_options}")
        _LOGGER.info(f"__init__. self.current_option={self.current_option}")

    async def async_select_option(self, option: str) -> None:
        # Возвращает первый найденный ключ
        value = next((k for k, v in self.addresses["base"]["select_values"].items() if v == option), None)
        await self.set_value("base", value)
        self.current_option = self.get_current_option()
        self.async_write_ha_state()

    def get_current_option(self):
        key = self.object.get_state(self.id)
        return self.addresses["base"]["select_values"][key]