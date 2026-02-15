from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback


class WirenboardSensor(SensorEntity):
    def __init__(self, coordinator, device, channel):
        self.coordinator = coordinator
        self.device = device
        self.channel = channel

    @property
    def available(self):
        return self.coordinator.last_update_success

    async def async_added_to_hass(self):
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self):
        self.async_write_ha_state()

    @property
    def native_value(self):
        device_key = f"{self.device['host']}:{self.device['port']}:{self.device['slave_id']}"
        key = f"{device_key}:temperature"
        return self.coordinator.data.get(key)