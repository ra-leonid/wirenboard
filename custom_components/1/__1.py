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


async def async_read_discrete_inputs(client, address, count, device_id:int):
    try:
        # Используем device_id для pymodbus 3.11.1
        result = await client.read_discrete_inputs(address, count=count, device_id=device_id)
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

async def read_registers_mr(device_id, port):
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

    firmware_version = await read_input_registers_string(client=client, address=250, count=16, device_id=device_id)
    bootloader = await read_input_registers_string(client=client, address=330, count=7, device_id=device_id)
    serial_number_byte = await read_holding_register_uint16(client=client,address=270,count=2,device_id=device_id)
    model = await read_input_registers_string(client=client, address=200, count=20, device_id=device_id)
    v3 = await read_input_registers(client=client, address=4, count=1, device_id=device_id)

    print(f"model={model}")
    print(f"model={model.replace("-", "_").lower()}")
    print(f"firmware_version={firmware_version}")
    print(f"bootloader={bootloader}")
    print(f"serial_number_byte={serial_number_byte}")
    serial_number = client.convert_from_registers(serial_number_byte, client.DATATYPE.UINT32)
    print(f"serial_number={serial_number}")

    client.close()

async def read_registers_mcm8(device_id, port):
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

    inputs = await async_read_discrete_inputs(client=client, address=0, count=8, device_id=device_id)
    # inputs_mode = await read_holding_register_bits(client=client, address=9, count=8, device_id=device_id)
    inputs_mode1 = await read_holding_register_uint16(client=client, address=9, count=8, device_id=device_id)

    print(f"inputs={inputs}")
    print(f"inputs_mode={inputs_mode}")
    print(f"inputs_mode1={inputs_mode1}")

    client.close()

# Модель устройства

# asyncio.run(read_registers(200,20,116, 502))
# asyncio.run(read_registers(200,20,247, 503))
# asyncio.run(read_registers(200,20,73, 502))
# asyncio.run(read_registers(200,20,50, 502))
# asyncio.run(read_registers_mr(116, 502))

# asyncio.run(read_registers_mcm8(69, 502))

n = 10
my_list = list(range(n))
print(my_list) # [0, 1, 2, ..., 9]

n = 10
keys = list(range(5, n))
print(keys) # [0, 1, 2, ..., 9]

values = [1]*len(keys)
print(values)

dictionary = dict(zip(keys, values))
print(dictionary)

my_list = [f"{i}" for i in range(1, 6)]
print(my_list)

dictionary = dict(zip(my_list, values))
print(dictionary)
dictionary.update({"w2":3})
print(dictionary)

from enum import Enum

class Color(Enum):
    RED = "R", 1
    GREEN = "G", 2

# Получение значения
print(Color.RED.value[0])
print(Color.RED.value[1])


def add_group_states(states: dict, addr_group: dict, base_states: list, slave_states: dict) -> dict:
    # states = {}
    # addr_group = {"type":RegisterType.coil,"start_address":0,"count":3,"field_format":FieldFormat.U16,
    #      "slaves":[
    #           {"name":"brightness","type":RegisterType.holding, "start_address":0, "count":3,"field_format":FieldFormat.U16},
    #       ]
    #  }
    # base_states = [True,False,False]
    # slave_states = {"brightness":[50,70,20]}

    count: int = addr_group["count"]
    for i in range(count):
        state = {"base": base_states[i]}
        for key, value in slave_states.items():
            state[key] = value[i]

        states[states["index"]+i] = state

    # На выходе получаем:
    # states = {0:{"base":True, "brightness":50}, 1:{"base":False, "brightness":70}, 2:{"base":False, "brightness":20}}
    states["index"] = states["index"] + count

    return states


class RegisterType(Enum):
    coil = 1
    holding = 2
    discrete_input = 3

class FieldFormat(Enum):
    BOOL = 1
    U16 = 2
    U32 = 3

# НАСТРОЙКА
addresses_group = [
    {"type": "coil", "start_address": 0, "count": 3, "field_format": "U16",
     "slaves": [
         {"name": "brightness", "type": "holding", "start_address": 0, "count": 3,
          "field_format": "U16"},
     ]
     }
]

# АДРЕСА

# ЗНАЧЕНИЯ, ГДЕ 0, 1, 2 - ЭТО ИНДЕКС УСТРОЙСТВА
__entity_values = [{"base":True, "brightness":50}, {"base":False, "brightness":70}, {"base":False, "brightness":20}]

# АДРЕСА В ENTITY
addresses = {
    "base": {"address": 0, "type": FieldFormat.U16},
    "brightness": {"address": 0, "type": FieldFormat.U16}
}

addresses_group = [
    {"type": RegisterType.holding, "start_address": 1147, "count": 1, "field_format": FieldFormat.U16},
    {"type": RegisterType.holding, "start_address": 1140, "count": 6, "field_format": FieldFormat.U16},
]

__registers_values = {"index":0}
for address_group in addresses_group:
    values = [None] * address_group["count"]

    slave_values = {}
    for slave in address_group.get("slaves", []):
        slave_values[slave["name"]] = values

    add_group_states(__registers_values, address_group, values, slave_values)

__registers_values.pop("index")

print(__registers_values)

# 2026-02-16 18:13:01.646 INFO (MainThread) [custom_components.wirenboard.coordinator] set_register_value на входе device_id=73; register_type=RegisterType.coil; addr=0; value=False
# 2026-02-16 18:13:01.716 INFO (MainThread) [custom_components.wirenboard.coordinator] set_register_value вернуло True




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

# select __init__.
addresses={
    'base':
        {'address': 16,
         'type': RegisterType.holding,
         'select_values':
             {2: 'Отключить все выходы',
              3: 'Управление отключено, вход измеряет частоту',
              4: 'Управлять по mapping-матрице',
              6: 'Управлять по mapping-матрице для кнопок'}
         }
}

# select get_current_option.
key=False
addresses={
    'base':
        {'address': 16,
         'type': RegisterType.holding,
         'select_values':
             {2: 'Отключить все выходы',
              3: 'Управление отключено, вход измеряет частоту',
              4: 'Управлять по mapping-матрице',
              6: 'Управлять по mapping-матрице для кнопок'}
         }
}

entity_values=[
    {'base': False},
    {'base': False},
    {'base': False},
    {'base': False},
    {'base': False},
    {'base': False},
    {'base': 2},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0},
    {'base': 0}, {'base': 0}, {'base': 0}, {'base': 0}, {'base': 0}, {'base': 0}, {'base': 0}, {'base': 0}, {'base': 0},
    {'base': 0}, {'base': 0}, {'base': 0}, {'base': 50}, {'base': 50}, {'base': 50}, {'base': 50}, {'base': 50}, {'base': 50},
    {'base': 50}, {'base': 1000}, {'base': 1000}, {'base': 1000}, {'base': 1000}, {'base': 1000}, {'base': 1000}, {'base': 1000},
    {'base': 300}, {'base': 300}, {'base': 300}, {'base': 300}, {'base': 300}, {'base': 300}, {'base': 300}
]
