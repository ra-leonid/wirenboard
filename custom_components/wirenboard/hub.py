from __future__ import annotations
from pymodbus import pymodbus_apply_logging_config
import datetime
from pymodbus import ModbusException
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.framer import FramerType
from homeassistant.core import HomeAssistant
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)
# pymodbus_apply_logging_config("DEBUG")

class modbus_hub:
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
        self._is_connected = False
        # Семафор для предотвращения параллельных запросов
        self._request_semaphore = asyncio.Semaphore(1)

    async def connect(self):
        try:
            if not self._client.connected:
                await self._client.connect()
            self._is_connected = True
        except asyncio.CancelledError:
            _LOGGER.debug(f"Подключение к Modbus {self._host}:{self._port} было отменено")
            self._is_connected = False
            raise
        except Exception as e:
            _LOGGER.error(f"Ошибка подключения к Modbus {self._host}:{self._port}: {e}")
            self._is_connected = False
            raise ValueError(f"Не удалось подключиться к устройству: {e}")

    async def disconnect(self):
        if self._client.connected:
            await self._client.close()
        self._is_connected = False

    async def read_holding_register_uint16(self, address, count, device_id:int):
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
                    return result.registers[0]
                return None
            except Exception as e:
                _LOGGER.debug(f"Ошибка при чтении регистра {address}: {e}")
                return None

    async def read_holding_register_uint32(self, address, count, device_id:int):
        async with self._request_semaphore:
            try:
                # Проверяем подключение и переподключаемся при необходимости
                if not self._client.connected:
                    await self.connect()
                
                # Используем device_id для pymodbus 3.11.1
                result = await self._client.read_holding_registers(address, count=count, device_id=device_id)
                if result.isError():
                    _LOGGER.debug(f"Ошибка Modbus при чтении 32-битного регистра {address}: {result}")
                    return None
                
                if result.registers and len(result.registers) >= 2:
                    # Convert two 16-bit registers to 32-bit value
                    high_register = result.registers[0]
                    low_register = result.registers[1]
                    return (high_register << 16) | low_register
                return None
            except Exception as e:
                # Не логируем ошибки подключения как предупреждения, только как отладочные сообщения
                if "Not connected" in str(e) or "Connection" in str(e):
                    _LOGGER.debug(f"Ошибка подключения при чтении 32-битного регистра {address}: {e}")
                else:
                    _LOGGER.warning(f"Ошибка при чтении 32-битного регистра {address}: {e}")
                return None

    async def read_holding_register_bits(self, address, count, device_id:int):
        async with self._request_semaphore:
            try:
                # Проверяем подключение и переподключаемся при необходимости
                if not self._client.connected:
                    await self.connect()
                
                # Используем device_id для pymodbus 3.11.1
                result = await self._client.read_holding_registers(address, count=count, device_id=device_id)
                if result.isError():
                    _LOGGER.debug(f"Ошибка Modbus при чтении битов регистра {address}: {result}")
                    return None
                
                if result.registers:
                    uint = result.registers[0]
                    bitlist = [int(x) for x in bin(uint)[2:]]
                    while len(bitlist) < 16:
                        bitlist.insert(0, 0)
                    return bitlist
                return None
            except Exception as e:
                # Не логируем ошибки подключения как предупреждения, только как отладочные сообщения
                if "Not connected" in str(e) or "Connection" in str(e):
                    _LOGGER.debug(f"Ошибка подключения при чтении битов регистра {address}: {e}")
                else:
                    _LOGGER.warning(f"Ошибка при чтении битов регистра {address}: {e}")
                return None

    async def write_holding_register_bits(self, address, bits, device_id:int) -> None:
        async with self._request_semaphore:
            try:
                # Проверяем подключение и переподключаемся при необходимости
                if not self._client.connected:
                    await self.connect()
                
                value = 0
                for bit in bits:
                    value = (value << 1) | bit
                
                # Используем device_id для pymodbus 3.11.1
                result = await self._client.write_register(address, value, device_id=device_id)
                if result.isError():
                    _LOGGER.warning(f"Ошибка Modbus при записи битов в регистр {address}: {result}")
                    raise Exception(f"Modbus write error: {result}")
            except Exception as e:
                _LOGGER.warning(f"Ошибка при записи битов в регистр {address}: {e}")
                raise

    async def write_holding_register(self, address, value, device_id:int) -> None:
        async with self._request_semaphore:
            try:
                # Проверяем подключение и переподключаемся при необходимости
                if not self._client.connected:
                    await self.connect()
                
                # Используем device_id для pymodbus 3.11.1
                result = await self._client.write_register(address, value, device_id=device_id)
                if result.isError():
                    _LOGGER.warning(f"Ошибка Modbus при записи значения {value} в регистр {address}: {result}")
                    raise Exception(f"Modbus write error: {result}")
            except Exception as e:
                _LOGGER.warning(f"Ошибка при записи значения {value} в регистр {address}: {e}")
                raise
    async def read_coils(self, address, count, device_id:int):
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
                    _LOGGER.warning(f"Ошибка при чтении битов регистра {address}: {e}")
                return None

    async def write_coils(self, address, value:list, device_id:int) -> None:
        async with self._request_semaphore:
            try:
                # Проверяем подключение и переподключаемся при необходимости
                if not self._client.connected:
                    await self.connect()

                # Используем device_id для pymodbus 3.11.1
                result = await self._client.write_coils(address, value, device_id=device_id)
                if result.isError():
                    _LOGGER.warning(f"Ошибка Modbus при записи значения {value} в регистр {address}: {result}")
                    raise Exception(f"Modbus write error: {result}")
            except Exception as e:
                _LOGGER.warning(f"Ошибка при записи значения {value} в регистр {address}: {e}")
                raise