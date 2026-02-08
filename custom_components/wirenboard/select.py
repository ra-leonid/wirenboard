import logging

from homeassistant.components.select import SelectEntity
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
    for obj in device.selects:
        for i in range(obj.count):
            objects.append(WbSelect(hass, coordinator, obj, i))

    _LOGGER.info(f"📊 СОЗДАНО {len(objects)} ПОЛЕЙ ВЫБОРА")
    async_add_entities(objects, update_before_add=False)


class WbSelect(WbEntity, CoordinatorEntity, SelectEntity):
    _attr_current_option: str | None = None
    _attr_entity_registry_enabled_default = True
    _attr_icon = "mdi:list-status"
    def __init__(
            self,
            hass: HomeAssistant,
            coordinator: WBCoordinator,
            obj,
            idx: int
    ) -> None:
        super().__init__(hass, obj, idx)
        CoordinatorEntity.__init__(self, coordinator)

        # self._attr_has_entity_name = True # Этого реквизита нет в классе WbEntity
        # self._attr_available = True # Этого реквизита нет в классе WbEntity

        self._attr_options = obj.get_attr_options(self.id)
        self.current_option = self.get_current_option()

    async def async_select_option(self, option: str) -> None:
        await self.object.set_value(self.id, option)
        self.current_option = self.get_current_option()
        self.async_write_ha_state()

    def get_current_option(self):
        return self.object.get_state(self.id)
