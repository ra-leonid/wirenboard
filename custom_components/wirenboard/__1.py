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


async def run1():
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


asyncio.run(run1())