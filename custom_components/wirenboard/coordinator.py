from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from .device import WBSmart, RegisterType
from .hub import async_modbus_hub


_LOGGER = logging.getLogger(__name__)

class WBCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config_entry):

        super().__init__(
            hass,
            _LOGGER,
            name="Wirenboard coordinator",
            config_entry=config_entry,
            update_interval=timedelta(seconds=1),
            always_update=True
        )

        self.__hubs = {}
        self.__devices = []

    async def async_will_remove_from_hass(self):
        """Вызывается перед удалением координатора."""
        for hub in self.__hubs.values():
            await hub.async_disconnect()
            # hub.disconnect()
            _LOGGER.warning(f"Разорвано соединение по Modbus с {hub.name}!")

    def get_hubs(self):
        return self.__hubs.values()

    @property
    def devices(self):
        return self.__devices

    def add_device(self, device):
        self.__devices.append(device)
        _LOGGER.debug(f"add_device. __devices={self.__devices}; host_ip={device.host_ip}; host_port={device.host_port}")

    async def _async_get_hub(self, host_ip:str, host_port:int):
        key = f"{host_ip}_{host_port}"
        hub = self.__hubs.get(key)
        _LOGGER.debug(f"_async_get_hub. Step1.  host_ip={host_ip}; host_port={host_port}; key={key}; hub={hub}; ")

        if hub is None:
            hub = async_modbus_hub(hass=self.hass, host=host_ip, port=host_port)
            if hub is None:
                return None

            self.__hubs[key] = hub

        _LOGGER.debug(f"_async_get_hub. Step2.  host_ip={host_ip}; host_port={host_port}; key={key}; hub={hub}; ")

        if await self._async_check_and_reconnect(hub):
            return hub
        return None

    async def _async_check_and_reconnect(self, hub:async_modbus_hub):
        """Проверяет подключение и пытается переподключиться при необходимости"""
        try:
            # Простая проверка - если клиент подключен, считаем что подключение есть
            if hub.connected:
                return True

            # Если не подключен, пытаемся подключиться
            _LOGGER.debug(f"Попытка подключения к устройству {hub.name}")
            await hub.connect()

            # Добавляем небольшую задержку после подключения для стабилизации
            await asyncio.sleep(0.2)

            _LOGGER.debug(f"Успешно подключились к устройству {hub.name}")
            return True
        except Exception as e:
            _LOGGER.error(f"Не удалось подключиться к устройству {hub.name}: {e}")
            return False
    
    async def update_devises(self, setup:bool):
        for device in self.__devices:
            hub = await self._async_get_hub(device.host_ip, device.host_port)
            
            if hub is None:
                device.connected = False
                continue

            if setup:
                await device.init_update(hub)

            await device.update(hub)

            _LOGGER.debug(f"_async_setup. Обновлено {device.name}")

    async def _async_setup(self):
        _LOGGER.debug(f"_async_setup")
        await self.update_devises(True)

    async def _async_update_data(self):
        _LOGGER.debug(f"_async_update_data")
        await self.update_devises(False)

    async def async_add_device_entities(self, platform, ComponentClass, async_add_entities):
        entities = []

        for device in self.devices:
            for objects in device.get_objects(platform):
                index = 0
                for address_group in objects.addresses_group:
                    index, components_values = objects.get_component_values(address_group, index)
                    for values in components_values:
                        _LOGGER.debug(f"async_add_device_entities. values={values}")
                        entities.append(ComponentClass(self.hass, self, **values))

        async_add_entities(entities, update_before_add=False)
        _LOGGER.info(f"📊 СОЗДАНО {len(entities)} {platform.name}")

    async def set_register_value(
            self,
            host_ip:str,
            host_port:int,
            device_id:int,
            register_type:RegisterType,
            address: int,
            value
    ) -> bool:
        hub: async_modbus_hub = await self._async_get_hub(host_ip, host_port)
        if hub is None:
            return False

        _LOGGER.info(f"set_register_value на входе device_id={device_id}; register_type={register_type}; addr={address}; value={value}")
        match register_type:
            case RegisterType.coil:
                result = await hub.async_write_coils(address, [value], device_id)
            case RegisterType.holding:
                result = await hub.async_write_holding(address, value, device_id)
            case _:
                result = False

        _LOGGER.info(f"set_register_value вернуло {result}")
        # self.connected = result
        return result
