from __future__ import annotations
from pymodbus import pymodbus_apply_logging_config
import datetime
from pymodbus import ModbusException
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.framer import FramerType
from asyncio.exceptions import InvalidStateError

from homeassistant.core import HomeAssistant
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)
# pymodbus_apply_logging_config("DEBUG")

class async_modbus_hub:
    def __init__(self, hass: HomeAssistant, host, port) -> None:
        self._host = host
        self._port = port
        self._hass = hass
        self._client = AsyncModbusTcpClient(
            host=host,
            port=port,
            framer=FramerType.SOCKET,
            retries=5,
            timeout=10,
            reconnect_delay=2,
        )
        # self.__is_connected = False
        # Семафор для предотвращения параллельных запросов
        self._request_semaphore = asyncio.Semaphore(1)

    @property
    def name(self):
        return f"{self._host}:{self._port}"

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def connected(self) -> bool:
        return self._client.connected

    async def connect(self):
        try:
            if not self.connected:
                await self._client.connect()
            # self.__is_connected = True
        except asyncio.CancelledError:
            _LOGGER.debug(f"Подключение к Modbus {self._host}:{self._port} было отменено")
            # self.__is_connected = False
            raise
        except Exception as e:
            _LOGGER.error(f"Ошибка подключения к Modbus {self._host}:{self._port}: {e}")
            # self.__is_connected = False
            raise ValueError(f"Не удалось подключиться к устройству: {e}")

    def disconnect(self):
        if self._client.connected:
            self._client.close()
        # self.__is_connected = False

    async def async_read_coils(self, address, count, device_id:int):
        async with self._request_semaphore:
            try:
                # Проверяем подключение и переподключаемся при необходимости
                if not self._client.connected:
                    await self.connect()

                # Используем device_id для pymodbus 3.11.1
                result = await self._client.read_coils(address, count=count, device_id=device_id)
                if result.isError():
                    _LOGGER.debug(f"Ошибка Modbus при чтении битов регистра {address}: {result}")
                    return None

                if result.bits:
                    bits = result.bits
                    del bits[count:len(bits)]
                    return bits
                return None
            except Exception as e:
                # Не логируем ошибки подключения как предупреждения, только как отладочные сообщения
                if "Not connected" in str(e) or "Connection" in str(e):
                    _LOGGER.debug(f"Ошибка подключения при чтении битов регистра {address}: {e}")
                else:
                    _LOGGER.debug(f"Ошибка при чтении битов регистра {address}: {e}")
                return None

    async def async_read_discrete_inputs(self, address, count, device_id:int):
        async with self._request_semaphore:
            try:
                # Проверяем подключение и переподключаемся при необходимости
                if not self._client.connected:
                    await self.connect()

                # Используем device_id для pymodbus 3.11.1
                result = await self._client.read_discrete_inputs(address, count=count, device_id=device_id)
                if result.isError():
                    _LOGGER.debug(f"Ошибка Modbus при чтении битов регистра {address}: {result}")
                    return None

                if result.bits:
                    bits = result.bits
                    del bits[count:len(bits)]
                    return bits
                return None
            except Exception as e:
                # Не логируем ошибки подключения как предупреждения, только как отладочные сообщения
                if "Not connected" in str(e) or "Connection" in str(e):
                    _LOGGER.debug(f"Ошибка подключения при чтении битов регистра {address}: {e}")
                else:
                    _LOGGER.debug(f"Ошибка при чтении битов регистра {address}: {e}")
                return None

    async def async_read_inputs(self, address, count, device_id:int):
        async with self._request_semaphore:
            try:
                # Проверяем подключение и переподключаемся при необходимости
                if not self._client.connected:
                    await self.connect()

                result = await self._client.read_input_registers(address, count=count, device_id=device_id)
                if result.isError():
                    _LOGGER.debug(f"Ошибка Modbus при чтении битов регистра {address}: {result}")
                    return None

                if result.registers:
                    return result.registers
                return None
            except Exception as e:
                # Не логируем ошибки подключения как предупреждения, только как отладочные сообщения
                if "Not connected" in str(e) or "Connection" in str(e):
                    _LOGGER.debug(f"Ошибка подключения при чтении битов регистра {address}: {e}")
                else:
                    _LOGGER.debug(f"Ошибка при чтении битов регистра {address}: {e}")
                return None

    async def async_read_holding_string(self, address, count, device_id: int):
        async with self._request_semaphore:
            try:
                # Проверяем подключение и переподключаемся при необходимости
                if not self._client.connected:
                    await self.connect()

                result = await self._client.read_holding_registers(address, count=count, device_id=device_id)
                if result.isError():
                    _LOGGER.debug(f"Ошибка Modbus при чтении регистра {address}: {result}")
                    return ""

                if result.registers:
                    while result.registers and result.registers[-1] == 0:
                        result.registers.pop()
                    return "".join(map(chr, result.registers))
                return None
            except Exception as e:
                _LOGGER.debug(f"Ошибка при чтении регистра {address}: {e}")
                return ""

    async def async_read_holding(self, address, count, device_id:int):
        async with self._request_semaphore:
            try:
                # Проверяем подключение и переподключаемся при необходимости
                if not self._client.connected:
                    await self.connect()
                
                result = await self._client.read_holding_registers(address, count=count, device_id=device_id)
                if result.isError():
                    _LOGGER.debug(f"Ошибка Modbus при чтении регистра {address}: {result}")
                    return None

                _LOGGER.debug(f"async_read_holding. result={result} device_id={device_id} address={address}")

                if result.registers:
                    return result.registers
                return None
            except Exception as e:
                _LOGGER.debug(f"Ошибка при чтении регистра {address}: {e}")
                return None

    async def async_read_holding_uint32(self, address, count, device_id: int):
        async with self._request_semaphore:
            try:
                # Проверяем подключение и переподключаемся при необходимости
                if not self._client.connected:
                    await self.connect()

                result = await self._client.read_holding_registers(address, count=count, device_id=device_id)
                if result.isError():
                    _LOGGER.debug(f"Ошибка Modbus при чтении регистра {address}: {result}")
                    return None

                if result.registers:
                    return self._client.convert_from_registers(result.registers, self._client.DATATYPE.UINT32)
                return None
            except Exception as e:
                _LOGGER.debug(f"Ошибка при чтении регистра {address}: {e}")
                return None

    async def async_write_coils(self, address, value:list, device_id:int) -> bool:
        async with self._request_semaphore:
            try:
                # Проверяем подключение и переподключаемся при необходимости
                if not self._client.connected:
                    await self.connect()

                # Используем device_id для pymodbus 3.11.1
                result = await self._client.write_coils(address, value, device_id=device_id)
                if result.isError():
                    _LOGGER.debug(f"Ошибка Modbus device_id {device_id} при записи значения {value} в регистр {address}: {result}")
                    raise Exception(f"Modbus write error: {result}")
            except TimeoutError:
                _LOGGER.warning("Pulling timed out")
                return False
            except ModbusException as value_error:
                _LOGGER.warning(f"Error write config register, modbus Exception {value_error.string}")
                return False
            except InvalidStateError as ex:
                _LOGGER.error(f"InvalidStateError Exceptions")
                return False
            except Exception as e:
                _LOGGER.debug(f"Ошибка при записи значения {value} в регистр {address}: {e}")
                raise
            return True

    async def async_write_holding(self, address, value, device_id:int) -> bool:
        async with self._request_semaphore:
            try:
                # Проверяем подключение и переподключаемся при необходимости
                if not self._client.connected:
                    await self.connect()

                result = await self._client.write_register(address, value, device_id=device_id)
                if result.isError():
                    _LOGGER.error(f"Ошибка Modbus при записи значения {value} в регистр {address}: {result}")
                    raise Exception(f"Modbus write error: {result}")
            except TimeoutError:
                _LOGGER.warning("Pulling timed out")
                return False
            except ModbusException as value_error:
                _LOGGER.warning(f"Error write config register, modbus Exception {value_error.string}")
                return False
            except InvalidStateError as ex:
                _LOGGER.error(f"InvalidStateError Exceptions")
                return False
            except Exception as e:
                _LOGGER.debug(f"Ошибка при записи значения {value} в регистр {address}: {e}")
                raise
            return True
