from __future__ import annotations
import asyncio
import logging


logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)
from pymodbus.client import AsyncModbusTcpClient
from pymodbus import ModbusException
from asyncio.exceptions import InvalidStateError

# settings for USB-RS485 adapter
#SERIAL = '/dev/cu.SLAB_USBtoUART'
#BAUD = 19200

# set Modbus defaults

#Defaults.UnitId = 1
#Defaults.Retries = 5
_LOGGER = logging.getLogger(__name__)


async def async_get_modbus_client(port):
    client = AsyncModbusTcpClient(
        host='192.168.0.7',
        port= port,
        #framer = FramerType.SOCKET,
        retries = 5,
        timeout = 10,
        reconnect_delay = 2,
    )
    try:
        await client.connect()
    except asyncio.CancelledError:
        _LOGGER.debug(f"Подключение к Modbus было отменено")
        raise
    except Exception as e:
        _LOGGER.error(f"Ошибка подключения к Modbus: {e}")
        raise ValueError(f"Не удалось подключиться к устройству: {e}")

    # client.close()
    return client

async def async_read_coils(client, address, count, device_id:int):
     try:

        result = await client.read_coils(address, count=count, device_id=device_id)
        if result.isError():
            print(f"Ошибка Modbus при чтении битов регистра {address}: {result}")
            return None

        if result.bits:
            bits = result.bits
            del bits[count:len(bits)]
            return bits
        return None
     except Exception as e:
        # Не логируем ошибки подключения как предупреждения, только как отладочные сообщения
        if "Not connected" in str(e) or "Connection" in str(e):
            print(f"Ошибка подключения при чтении битов регистра {address}: {e}")
        else:
            print(f"Ошибка при чтении битов регистра {address}: {e}")
        return None

async def async_write_coils(client, address, value:list, device_id:int) -> bool:
    try:
        print(value)
        result = await client.write_coils(address, value, device_id=device_id)
        if result.isError():
            print(f"Ошибка Modbus device_id {device_id} при записи значения {value} в регистр {address}: {result}")
            raise Exception(f"Modbus write error: {result}")
    except TimeoutError:
        print("Pulling timed out")
        return False
    except ModbusException as value_error:
        print(f"Error write config register, modbus Exception {value_error.string}")
        return False
    except InvalidStateError as ex:
        print(f"InvalidStateError Exceptions")
        return False
    except Exception as e:
        print(f"Ошибка при записи значения {value} в регистр {address}: {e}")
        raise
    return True

async def read_input_registers_string(client, address, count, device_id:int):
    try:
        # Проверяем подключение и переподключаемся при необходимости
        if not client.connected:
            await client.connect()

        result = await client.read_input_registers(address, count=count, device_id=device_id)
        if result.isError():
            _LOGGER.debug(f"Ошибка Modbus при чтении регистра {address}: {result}")
            return None

        if result.registers:
            while result.registers and result.registers[-1] == 0:
                result.registers.pop()
            return "".join(map(chr, result.registers))
        return None
    except Exception as e:
        _LOGGER.debug(f"Ошибка при чтении регистра {address}: {e}")
        return None

async def read_holding_register_uint16(client, address, count, device_id:int):
    try:
        # Проверяем подключение и переподключаемся при необходимости
        if not client.connected:
            await client.connect()

        result = await client.read_holding_registers(address, count=count, device_id=device_id)
        if result.isError():
            _LOGGER.debug(f"Ошибка Modbus при чтении регистра {address}: {result}")
            return None

        if result.registers:
            return result.registers
        return None
    except Exception as e:
        _LOGGER.debug(f"Ошибка при чтении регистра {address}: {e}")
        return None

async def read_coils():
    client = AsyncModbusTcpClient(
        host='192.168.0.7',
        port= 503,
        #framer = FramerType.SOCKET,
        retries = 5,
        timeout = 10,
        reconnect_delay = 2,
    )

    #connection = client.connect()
    try:
        await client.connect()
    except asyncio.CancelledError:
        _LOGGER.debug(f"Подключение к Modbus было отменено")
        raise
    except Exception as e:
        _LOGGER.error(f"Ошибка подключения к Modbus: {e}")
        raise ValueError(f"Не удалось подключиться к устройству: {e}")

    print("Readout started")

    #result = client.read_discrete_inputs(0)
    address=1000
    count=16
    device_id = 247
    # await client.write_coils(address, [True,True,True,True,True,True], device_id=116)
    # # Добавляем небольшую задержку после подключения для стабилизации
    # await asyncio.sleep(2.5)
    # await client.write_coils(address, [False,False,False,False,False,False], device_id=116)
    result = await client.read_coils(address,count=count,device_id=device_id)
    #result = client.read_input_registers(0,1)
    print(f"result={result}")
    bits = result.bits
    del bits[count:len(bits)]
    print(f"bits={bits}")

    result = await client.read_holding_registers(11000,count=6,device_id=device_id)
    result1 = await client.read_holding_registers(11500,count=6,device_id=device_id)
    print(f"result={result}")
    if result.registers:
        hex_strings = [hex(x) for x in result.registers]
        print(hex_strings)  # ['0xa', '0xff', '0x400', '0x3039']
    print(f"result={result}")

    if result1.registers:
        hex_strings = [hex(x) for x in result1.registers]
        print(hex_strings)  # ['0xa', '0xff', '0x400', '0x3039']

    if result.isError():
        _LOGGER.debug(f"Ошибка Modbus при чтении регистра {address}: {result}")

        # print(f"registers=result.registers[0]")

    client.close()

# client = asyncio.run(async_get_modbus_client(503))
# value = [False, False, False, False, False, False, False, True]
# result = asyncio.run(async_write_coils(client, 0, value, 73))
# result = asyncio.run(async_read_coils(client, 1000, 16, 247))
# result = asyncio.run(read_input_registers_string(client, 200, 1, 247))
# result = asyncio.run(read_holding_register_uint16(client, [990], 8, 247))
result = asyncio.run(read_coils())
print(result)

# client.close()

