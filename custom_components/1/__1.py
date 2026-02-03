from __future__ import annotations
import asyncio
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

#from pymodbus.constants import Endian
#from pymodbus.constants import Defaults
#from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client import ModbusTcpClient as ModbusClient
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.framer import FramerType

# settings for USB-RS485 adapter
#SERIAL = '/dev/cu.SLAB_USBtoUART'
#BAUD = 19200

# set Modbus defaults

#Defaults.UnitId = 1
#Defaults.Retries = 5
_LOGGER = logging.getLogger(__name__)


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

async def read_holding_register_bits(client, address, count, device_id:int):
    try:
        # Проверяем подключение и переподключаемся при необходимости
        if not client.connected:
            await client.connect()

        # Используем device_id для pymodbus 3.11.1
        result = await client.read_holding_registers(address, count=count, device_id=device_id)
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


async def read_coils():
    client = AsyncModbusTcpClient(
        host='192.168.0.7',
        port= 502,
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
    address=0
    count_=6
    await client.write_coils(address, [True,True,True,True,True,True], device_id=116)
    # Добавляем небольшую задержку после подключения для стабилизации
    await asyncio.sleep(2.5)
    await client.write_coils(address, [False,False,False,False,False,False], device_id=116)
    result = await client.read_coils(address,count=count_,device_id=116)
    #result = client.read_input_registers(0,1)
    print(f"result={result}")
    bits = result.bits
    del bits[count_:len(bits)]
    print(f"bits={bits}")

    if result.isError():
        _LOGGER.debug(f"Ошибка Modbus при чтении регистра {address}: {result}")

    if result.registers:
        print(f"registers=result.registers[0]")

    client.close()

async def read_holding():
    client = AsyncModbusTcpClient(
        host='192.168.0.7',
        port= 502,
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
    address=32
    count_=6
    #await client.write_coils(address, [True,True,True,True,True,True], device_id=116)
    # Добавляем небольшую задержку после подключения для стабилизации
    #await asyncio.sleep(2.5)
    #await client.write_coils(address, [False,False,False,False,False,False], device_id=116)
    result0 = await client.read_holding_registers(address, count=3, device_id=116)
    print(f"result0={result0}")

    result = await read_holding_register_uint16(client=client,address=address,count=count_,device_id=116)
    #result = client.read_input_registers(0,1)
    print(f"result={result}")
    result1 = await read_holding_register_bits(client=client,address=address,count=count_,device_id=116)
    #result = client.read_input_registers(0,1)
    print(f"result1={result1}")
    #bits = result.bits
    #del bits[count_:len(bits)]
    #print(f"bits={bits}")
    '''
    if result.isError():
        _LOGGER.debug(f"Ошибка Modbus при чтении регистра {address}: {result}")

    if result.registers:
        print(f"registers=result.registers[0]")
    '''

    client.close()

asyncio.run(read_holding())