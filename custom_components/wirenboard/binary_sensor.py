from __future__ import annotations

import logging
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant

from .device import Platform
from .const import DOMAIN
from .coordinator import WBCoordinator
from .entity import WbEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator: WBCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    await coordinator.async_add_device_entities(Platform.binary_sensor, WBBinarySensor, async_add_entities)


class WBBinarySensor(WbEntity, CoordinatorEntity, BinarySensorEntity):
    def __init__(
            self,
            hass: HomeAssistant,
            coordinator: WBCoordinator,
            **kwargs
    ) -> None:
        super().__init__(hass, **kwargs)
        CoordinatorEntity.__init__(self, coordinator)

        device_class = kwargs.get("device_class", None)
        if not device_class is None:
            self.device_class = kwargs['device_class']

        # _LOGGER.info(f"kwargs['inverted_inputs']={kwargs['inverted_inputs']}")
        self.invert = 'inverted_inputs' in kwargs and self.id+1 in kwargs['inverted_inputs']
        # _LOGGER.info(f"self.id={self.id}; kwargs['inverted_inputs']={kwargs['inverted_inputs']}; self.invert={self.invert}")

    # @property
    # def device_class(self) -> str:
    #     """Return device class."""
    #     return BinarySensorDeviceClass.WINDOW

    @property
    def is_on(self) -> bool:
        return self.object.get_state(self.id, "base") ^ self.invert # Инвертировать если self.invert = True
