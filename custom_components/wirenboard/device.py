from __future__ import annotations

import asyncio
import datetime
import logging
import async_timeout
from asyncio.exceptions import InvalidStateError
from bitstring import BitArray
from homeassistant.core import HomeAssistant
from pymodbus import ModbusException
from pymodbus.exceptions import ModbusIOException

from .hub import modbus_hub
from .registers import WBSmartRegisters

_LOGGER = logging.getLogger(__name__)
class WBSmart:
    def __init__(self, hass: HomeAssistant, name, host_ip: str, host_port: int, device_type:str, device_id: int) ->None:
        self._name = f"{device_type}-{device_id}"
        self._hass = hass
        self._device_type = device_type
        self._device_id = device_id

        self._hub = modbus_hub(hass=hass, host=host_ip, port=host_port)

        # Инициализируем атрибуты, которые используются в update()
        self._states  = [False, False, False, False, False, False]

        # Инициализируем битовые массивы
        self._config_bits = None

        # Флаг для отслеживания состояния подключения
        self._connection_attempts = 0
        self._is_connected = False

    # TODO реализовать вывод информации об устройстве "https://selectel.ru/blog/ha-karadio/" def device_info

    async def _check_and_reconnect(self):
        """Проверяет подключение и пытается переподключиться при необходимости"""
        try:
            # Простая проверка - если клиент подключен, считаем что подключение есть
            if hasattr(self._hub, '_client') and self._hub._client.connected:
                self._is_connected = True
                return True
            
            # Если не подключен, пытаемся подключиться
            _LOGGER.info(f"Попытка подключения к устройству {self._name}")
            await self._hub.connect()
            
            # Добавляем небольшую задержку после подключения для стабилизации
            await asyncio.sleep(0.2)
            
            self._is_connected = True
            _LOGGER.info(f"Успешно подключились к устройству {self._name}")
            return True
        except Exception as e:
            _LOGGER.error(f"Не удалось подключиться к устройству {self._name}: {e}")
            self._is_connected = False
            return False

    async def update(self):
        try:
            # Проверяем подключение
            if not await self._check_and_reconnect():
                _LOGGER.debug(f"Не удалось подключиться к устройству {self._name}, пропускаем обновление")
                self._is_connected = False
                return
                
            async with async_timeout.timeout(15):
                #self._config_bits = await self._hub.read_holding_register_bits(WBSmartRegisters.module_config, 6)
                self._config_bits = await self._hub.read_coils(0, 6, self._device_id)

                # Проверяем, что данные получены корректно
                if self._config_bits is None:
                    _LOGGER.debug("Не удалось получить конфигурационные биты модуля")
                    self._is_connected = False
                    return
                
                # Если данные получены успешно, считаем что подключение активно
                self._is_connected = True

                for i in range(6):
                    _LOGGER.warning(f"🔧 КАНАЛ[{i}=: connecting_sensors={self._config_bits[i]}")
                    self._states[i] = bool(self._config_bits[i])
        except TimeoutError:
            _LOGGER.warning(f"Polling timed out for {self._name} - устройство не отвечает")
            # Сбрасываем счетчик попыток, чтобы попробовать переподключиться в следующий раз
            self._connection_attempts = 0
            self._is_connected = False
            return
        except ModbusIOException as value_error:
            _LOGGER.warning(f"ModbusIOException for {self._name}: {value_error.string}")
            # Сбрасываем счетчик попыток, чтобы попробовать переподключиться в следующий раз
            self._connection_attempts = 0
            self._is_connected = False
            return
        except ModbusException as value_error:
            _LOGGER.warning(f"ModbusException for {self._name}: {value_error.string}")
            # Сбрасываем счетчик попыток, чтобы попробовать переподключиться в следующий раз
            self._connection_attempts = 0
            self._is_connected = False
            return
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exceptions for {self._name}")
            self._is_connected = False
            return
        except Exception as e:
            _LOGGER.error(f"Неожиданная ошибка при обновлении {self._name}: {e}")
            self._is_connected = False
            return

    def get_name(self):
        return self._name

    def get_switch_status(self,channel:int):
        return self._states[channel]

    async def write_config_register(self):
        try:
            async with async_timeout.timeout(5):
                #await self._hub.write_holding_register_bits(WBSmartRegisters.module_config, self._config_bits)
                await self._hub.write_coils(0, self._states.copy(), self._device_id)
        except TimeoutError:
            _LOGGER.warning("Pulling timed out")
            return
        except ModbusException as value_error:
            _LOGGER.warning(f"Error write config register, modbus Exception {value_error.string}")
            return
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exceptions")
            return

    async def set_switch_status(self,channel:int,state:bool):
        #self._first_group_valve_is_open = state
        _LOGGER.warning(f"До изменение состояния канала {channel}: state={state}; self._states={self._states}")
        self._states[channel] = state
        _LOGGER.warning(f"Изменен массив {channel}: state={state}; self._states={self._states}")
        await self.write_config_register()
        _LOGGER.warning(f"После изменение состояния канала {channel}: state={state}; self._states={self._states}")

    def is_connected(self):
        """Возвращает состояние подключения к устройству"""
        return self._is_connected
