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
from .registers import WBMRRegisters

_LOGGER = logging.getLogger(__name__)

class WBSmart:
    def __init__(self, hass: HomeAssistant, host_ip: str, host_port: int, device_type:str, device_id: int) ->None:
        self.__device_type = device_type.replace("-", "_")
        self.__device_id = device_id
        self.__name = f"{self.__device_type}_{self.__device_id}"
        self.__hass = hass

        self._hub = modbus_hub(hass=hass, host=host_ip, port=host_port)

        # Флаг для отслеживания состояния подключения
        # TODO Добавить код увеличения попыток
        self.__connection_attempts = 0
        self.__is_connected = False

    # TODO реализовать вывод информации об устройстве "https://selectel.ru/blog/ha-karadio/" def device_info

    def __del__(self):
        asyncio.run(self._hub.disconnect())
        _LOGGER.warning(f"Устройство {self.name} удалено. Отключено по Modbus")

    async def _check_and_reconnect(self):
        """Проверяет подключение и пытается переподключиться при необходимости"""
        try:
            # Простая проверка - если клиент подключен, считаем что подключение есть
            if hasattr(self._hub, '_client') and self._hub._client.connected:
                self.connected()
                return True
            
            # Если не подключен, пытаемся подключиться
            _LOGGER.warning(f"Попытка подключения к устройству {self.__name}")
            await self._hub.connect()
            
            # Добавляем небольшую задержку после подключения для стабилизации
            await asyncio.sleep(0.2)

            self.connected()
            _LOGGER.warning(f"Успешно подключились к устройству {self.__name}")
            return True
        except Exception as e:
            _LOGGER.error(f"Не удалось подключиться к устройству {self.__name}: {e}")
            self.disconnected()
            return False

    @property
    def name(self):
        return self.__name

    @property
    def device_type(self):
        return self.__device_type

    @property
    def device_id(self):
        return self.__device_id

    @property
    def is_connected(self):
        """Возвращает состояние подключения к устройству"""
        return self.__is_connected

    def connected(self):
        """Возвращает состояние подключения к устройству"""
        self.__is_connected = True

    def disconnected(self):
        """Возвращает состояние подключения к устройству"""
        self.__is_connected = False

    @property
    def connection_attempts(self):
        """Возвращает состояние подключения к устройству"""
        return self.__connection_attempts

    def inc_connection_attempts(self):
        self.__connection_attempts += 1

    def reset_connection_attempts(self):
        self.__connection_attempts = 0

    async def write_coil_registers(self, address:int, values):
        try:
            async with async_timeout.timeout(5):
                _LOGGER.debug(f"Запись в coil регистры {address} устройства {self.device_id} значения {values}")
                await self._hub.write_coils(address, values.copy(), self.device_id)
        except TimeoutError:
            _LOGGER.warning("Pulling timed out")
            return
        except ModbusException as value_error:
            _LOGGER.warning(f"Error write config register, modbus Exception {value_error.string}")
            return
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exceptions")
            return

    async def write_holding_register(self, address:int, value:int):
        try:
            async with async_timeout.timeout(5):
                _LOGGER.debug(f"Запись в holding регистр {address} устройства {self.device_id} значения {value}")
                await self._hub.write_holding_register(address, value, self.device_id)
        except TimeoutError:
            _LOGGER.warning("Pulling timed out")
            return False
        except ModbusException as value_error:
            _LOGGER.warning(f"Error write holding register, modbus Exception {value_error.string}")
            return False
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exceptions")
            return False
        return True


class WBMr(WBSmart, WBMRRegisters):
    def __init__(self, hass: HomeAssistant, host_ip: str, host_port: int, device_type: str,
                 device_id: int) -> None:

        super().__init__(hass, host_ip, host_port, device_type, device_id)

        # Инициализируем атрибуты, которые используются в update()
        self._states = [False]*6
        self._input_mode = [2] + [1]*(self.input_count - 1)
        self._status_outputs_when_power_applied = 0
        self._entry_trigger_count = [0]*self.input_count

    # TODO реализовать вывод информации об устройстве "https://selectel.ru/blog/ha-karadio/" def device_info

    async def update(self):
        try:
            # Проверяем подключение
            connecting_status = await self._check_and_reconnect()
            _LOGGER.debug(f"Metod update. connecting_status = {connecting_status}")
            if not connecting_status:
                _LOGGER.debug(f"Не удалось подключиться к устройству {self.name}, пропускаем обновление")
                self.disconnected()
                return

            async with async_timeout.timeout(15):
                result = await self._hub.read_coils(self.relay_statuses_addr, self.relay_count, self.device_id)

                # Проверяем, что данные получены корректно
                if result is None:
                    _LOGGER.debug(f"Не удалось получить состояния реле {self.name}")
                    self.disconnected()
                    return

                self._states = result

                # Счетчики срабатываний входов
                result = await self._hub.read_holding_register_uint16(self.entry_trigger_counter_addr, self.input_count-1, self.device_id)
                # Проверяем, что данные получены корректно
                if result is None:
                    _LOGGER.debug(f"Не удалось получить счетчики срабатываний входов модуля {self.name}")
                    self.disconnected()
                    return

                result0 = await self._hub.read_holding_register_uint16(self.entry_trigger_counter_0_addr, 1, self.device_id)
                # Проверяем, что данные получены корректно
                if result0 is None:
                    _LOGGER.debug(f"Не удалось получить режимы работы входа 0 модуля {self.name}")
                    self.disconnected()
                    return

                self._entry_trigger_count = result0 + result

                # Если данные получены успешно, считаем что подключение активно
                self.connected()


        except TimeoutError:
            _LOGGER.warning(f"Polling timed out for {self.name} - устройство не отвечает")
            # Сбрасываем счетчик попыток, чтобы попробовать переподключиться в следующий раз
            self.reset_connection_attempts()
            self.disconnected()
            return
        except ModbusIOException as value_error:
            _LOGGER.warning(f"ModbusIOException for {self.name}: {value_error.string}")
            # Сбрасываем счетчик попыток, чтобы попробовать переподключиться в следующий раз
            self.reset_connection_attempts()
            self.disconnected()
            return
        except ModbusException as value_error:
            _LOGGER.warning(f"ModbusException for {self.name}: {value_error.string}")
            # Сбрасываем счетчик попыток, чтобы попробовать переподключиться в следующий раз
            self.reset_connection_attempts()
            self.disconnected()
            return
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exceptions for {self.name}")
            self.disconnected()
            return
        except Exception as e:
            _LOGGER.error(f"Неожиданная ошибка при обновлении {self.name}: {e}")
            self.disconnected()
            return

    async def update_setting(self):
        try:
            connecting_status = await self._check_and_reconnect()
            _LOGGER.debug(f"Metod update_setting. connecting_status = {connecting_status}")
            if not connecting_status:
                _LOGGER.debug(f"Не удалось подключиться к устройству {self.name}, пропускаем обновление")
                self.disconnected()
                return

            async with async_timeout.timeout(15):

                # Состояние выходов при подаче питания
                result = await self._hub.read_holding_register_uint16(self.status_outputs_when_power_applied_addr, 1, self.device_id)
                # Проверяем, что данные получены корректно
                if result is None:
                    _LOGGER.debug(f"Не удалось получить 'Состояние выходов при подаче питания' модуля {self.name}")
                    self.disconnected()
                    return
                self._status_outputs_when_power_applied = result[0]

                # Режимы работы входов модуля
                result = await self._hub.read_holding_register_uint16(self.input_mode_addr, self.input_count-1, self.device_id)
                # Проверяем, что данные получены корректно
                if result is None:
                    _LOGGER.debug(f"Не удалось получить режимы работы входов модуля {self.name}")
                    self.disconnected()
                    return

                result0 = await self._hub.read_holding_register_uint16(self.input_mode_0_addr, 1, self.device_id)
                # Проверяем, что данные получены корректно
                if result0 is None:
                    _LOGGER.debug(f"Не удалось получить режимы работы входа 0 модуля {self.name}")
                    self.disconnected()
                    return

                # Если данные получены успешно, считаем что подключение активно
                self._input_mode = result0 + result

                self.connected()

        except TimeoutError:
            _LOGGER.warning(f"Polling timed out for {self.name} - устройство не отвечает")
            # Сбрасываем счетчик попыток, чтобы попробовать переподключиться в следующий раз
            self.reset_connection_attempts()
            self.disconnected()
            return
        except ModbusIOException as value_error:
            _LOGGER.warning(f"ModbusIOException for {self.name}: {value_error.string}")
            # Сбрасываем счетчик попыток, чтобы попробовать переподключиться в следующий раз
            self.reset_connection_attempts()
            self.disconnected()
            return
        except ModbusException as value_error:
            _LOGGER.warning(f"ModbusException for {self.name}: {value_error.string}")
            # Сбрасываем счетчик попыток, чтобы попробовать переподключиться в следующий раз
            self.reset_connection_attempts()
            self.disconnected()
            return
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exceptions for {self.name}")
            self.disconnected()
            return
        except Exception as e:
            _LOGGER.error(f"Неожиданная ошибка при обновлении {self.name}: {e}")
            self.disconnected()
            return

    def get_switch_status(self, channel: int):
        _LOGGER.debug(f"get_switch_status:  _states={self._states}; channel={channel}")
        return self._states[channel]

    def get_switch_input_mode(self, channel: int):
        key = self._input_mode[channel]
        if(channel == 0):
            return self.INPUT_MODE_VALUES_0[key]
        else:
            return self.INPUT_MODE_VALUES[key]

    def get_entry_trigger_count(self, channel: int):
        _LOGGER.debug(f"get_entry_trigger_count: channel={channel} count={self._entry_trigger_count[channel]}")
        return self._entry_trigger_count[channel]

    def get_status_outputs_when_power_applied(self):
        return self.STATUS_OUTPUTS_WHEN_POWER_APPLIED[self._status_outputs_when_power_applied]

    async def set_switch_status(self, channel: int, state: bool):
        _LOGGER.debug(f"set_switch_status 1:  _states={self._states}; channel={channel}")
        self._states[channel] = state
        await self.write_coil_registers(self.relay_statuses_addr, self._states)
        _LOGGER.debug(f"set_switch_status 2:  _states={self._states}; channel={channel}")

    async def set_input_mode(self, channel: int, option: str):
        if(channel == 0):
            dict_values = self.INPUT_MODE_VALUES_0
            address = self.input_mode_0_addr
        else:
            dict_values = self.INPUT_MODE_VALUES
            address = self.input_mode_addr + channel - 1

        # Возвращает первый найденный ключ
        option_key = next((k for k, v in dict_values.items() if v == option), None)

        if (await self.write_holding_register(address, option_key)):
            self._input_mode[channel] = option_key

    async def set_status_outputs_when_power_applied(self, option: str):
        # Возвращает первый найденный ключ
        option_key = next((k for k, v in self.STATUS_OUTPUTS_WHEN_POWER_APPLIED.items() if v == option), None)

        if (await self.write_holding_register(self.status_outputs_when_power_applied_addr, option_key)):
            self._status_outputs_when_power_applied = option_key

    def get_attr_options(self, select_type:str, channel:int | None = None):
        _LOGGER.debug(f"get_attr_options:  select_type={select_type}; channel={channel}")
        match select_type:
            case "input_mode":
                if (channel==0):
                    _LOGGER.debug(f"self.INPUT_MODE_VALUES_0.values()={self.INPUT_MODE_VALUES_0.values()}")
                    return list(self.INPUT_MODE_VALUES_0.values())
                else:
                    _LOGGER.debug(f"self.INPUT_MODE_VALUES.values()={self.INPUT_MODE_VALUES.values()}")
                    return list(self.INPUT_MODE_VALUES.values())
            case "status_outputs_when_power_applied":
                _LOGGER.debug(f"self.STATUS_OUTPUTS_WHEN_POWER_APPLIED.values()={self.STATUS_OUTPUTS_WHEN_POWER_APPLIED.values()}")
                return list(self.STATUS_OUTPUTS_WHEN_POWER_APPLIED.values())
            case _:
                return list()