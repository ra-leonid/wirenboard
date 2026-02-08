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

async def read_input_registers(client, address, count, device_id:int):
    try:
        # Проверяем подключение и переподключаемся при необходимости
        if not client.connected:
            await client.connect()

        result = await client.read_input_registers(address, count=count, device_id=device_id)
        if result.isError():
            _LOGGER.debug(f"Ошибка Modbus при чтении регистра {address}: {result}")
            return None

        if result.registers:
            return result.registers
        return None
    except Exception as e:
        _LOGGER.debug(f"Ошибка при чтении регистра {address}: {e}")
        return None

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
    count=6
    await client.write_coils(address, [True,True,True,True,True,True], device_id=116)
    # Добавляем небольшую задержку после подключения для стабилизации
    await asyncio.sleep(2.5)
    await client.write_coils(address, [False,False,False,False,False,False], device_id=116)
    result = await client.read_coils(address,count=count,device_id=116)
    #result = client.read_input_registers(0,1)
    print(f"result={result}")
    bits = result.bits
    del bits[count:len(bits)]
    print(f"bits={bits}")

    if result.isError():
        _LOGGER.debug(f"Ошибка Modbus при чтении регистра {address}: {result}")

    if result.registers:
        print(f"registers=result.registers[0]")

    client.close()

async def read_holding(address, count, device_id, port):
    client = AsyncModbusTcpClient(
        host='192.168.0.7',
        port= port,
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
    # address=32
    # count=6
    #await client.write_coils(address, [True,True,True,True,True,True], device_id=116)
    # Добавляем небольшую задержку после подключения для стабилизации
    #await asyncio.sleep(2.5)
    #await client.write_coils(address, [False,False,False,False,False,False], device_id=116)
    # result0 = await client.read_holding_registers(address, count=3, device_id=device_id)
    # print(f"result0={result0}")
    #
    # result = await read_holding_register_uint16(client=client,address=address,count=count,device_id=device_id)
    # print(f"result={result}")
    # result1 = await read_holding_register_bits(client=client,address=address,count=count,device_id=device_id)
    # print(f"result1={result1}")

    model = await read_input_registers_string(client=client, address=200, count=20, device_id=device_id)
    firmware_version = await read_input_registers_string(client=client, address=250, count=16, device_id=device_id)
    bootloader = await read_input_registers_string(client=client, address=330, count=7, device_id=device_id)
    serial_number_byte = await read_holding_register_uint16(client=client,address=270,count=2,device_id=device_id)

    print(f"model={model}")
    print(f"firmware_version={firmware_version}")
    print(f"bootloader={bootloader}")
    print(f"serial_number_byte={serial_number_byte}")
    serial_number = client.convert_from_registers(serial_number_byte, client.DATATYPE.UINT32)
    print(f"serial_number={serial_number}")
    # print(f"UTFFFFF={client.convert_from_registers(result2, client.DATATYPE.UINT64)}")
    # a= "".join(map(chr, result2))
    # print(f"a={a}")
    #
    #
    # print(f"UTFFFFF={client.convert_from_registers(result2, client.DATATYPE.UINT64)}")
    # print(f"UTFFFFF={client.convert_from_registers(result2, client.DATATYPE.INT64)}")

    #bits = result.bits
    #del bits[count:len(bits)]
    #print(f"bits={bits}")
    '''
    if result.isError():
        _LOGGER.debug(f"Ошибка Modbus при чтении регистра {address}: {result}")

    if result.registers:
        print(f"registers=result.registers[0]")
    '''

    client.close()

    # return result2
# Модель устройства

asyncio.run(read_holding(200,20,116, 502))


# asyncio.run(read_holding(266,4))

# Версия прошивки в числовом формате, Только в версиях прошивок, где есть Быстрый Modbus
# asyncio.run(read_holding(320,4)) # Последний, это суффикс. Если не 0 - преобразовать
# Версия прошивки. Требуется преобразование в символы
# asyncio.run(read_holding(250,16))
#
# asyncio.run(read_holding(320,6))
# asyncio.run(read_holding(326,2))

# asyncio.run(read_holding(266,6,116))
# asyncio.run(read_holding(290,12,116))
# asyncio.run(read_holding(220,25,116))
# asyncio.run(read_holding(266,6,247, 503))
# asyncio.run(read_holding(266,6,116, 502))

# # Серийные номера
# mge = asyncio.run(read_holding(270,2,116, 502))
# mr6c = asyncio.run(read_holding(270,2,247, 503))
# mr6c1 = asyncio.run(read_holding(266,4,247, 503))
# b = (mge[0] << 16) | mge[1]
# print(f"mge={b}")
# b1 = (mr6c[0] << 16) | mr6c[1]
# print(f"mr6c={b1}")
# # Декодируем (уточните byte/word order в мануале устройства)
# # decoder = BinaryPayloadDecoder.fromRegisters(mr6c1, byteorder=Endian.Big, wordorder=Endian.Big)
# # value = decoder.decode_64bit_uint()
# # print(f"value={value}")
# c = (mr6c1[0] << 24) + (mr6c1[1] << 16)  + (mr6c1[2] << 8) + mr6c1[3]
# print(f"mr6c1={c}")
# c = (mr6c1[3] << 24) + (mr6c1[2] << 16)  + (mr6c1[1] << 8) + mr6c1[0]
# print(f"mr6c1={c}")
#
# c = (mr6c1[0] << 24) + (mr6c1[1] << 16)  + (mr6c1[2] << 8) + mr6c1[3]
# print(f"mr6c1={c}")
# c = (mr6c1[3] << 24) + (mr6c1[2] << 16)  + (mr6c1[1] << 8) + mr6c1[0]
# print(f"mr6c1={c}")
#
# U64 = (mr6c1[0] << 48) | (mr6c1[1] << 32) | (mr6c1[2] << 16) | mr6c1[3]
# print(f"U64={U64}")
# U64 = (mr6c1[3] << 48) | (mr6c1[2] << 32) | (mr6c1[1] << 16) | mr6c1[0]
# print(f"U64={U64}")


# asyncio.run(read_holding(266,4,247, 503))