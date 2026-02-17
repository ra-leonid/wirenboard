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

client = asyncio.run(async_get_modbus_client(502))
value = [False, False, False, False, False, False, False, True]
result = asyncio.run(async_write_coils(client, 0, value, 73))
print(result)

client.close()
