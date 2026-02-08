from __future__ import annotations

from enum import Enum
import asyncio
import time
import logging
import async_timeout
from asyncio.exceptions import InvalidStateError
# from bitstring import BitArray
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from pymodbus import ModbusException
from pymodbus.exceptions import ModbusIOException

from .hub import async_modbus_hub
# from .registers import WBMRRegisters
from .const import (
INPUT_MODE_VALUES,
INPUT_MODE_VALUES_0,
STATUS_OUTPUTS_WHEN_POWER_APPLIED
)

_LOGGER = logging.getLogger(__name__)


class Platform(Enum):
    binary_sensor = 1
    sensor = 2
    select = 3
    switch = 4

class RegisterType(Enum):
    coil = 1
    holding = 2
    sensor = 3

class GroupAddresses:
    def __init__(self, start_address: int, count: int):
        self.start_address = start_address
        self.count = count

class DeviceObjectGroup:
    def __init__(self, **kwargs):
        self.__device = kwargs["device"]
        self.__name = kwargs["name"]
        self.__name_id = kwargs.get("name_id", "")
        self.__platform = kwargs["platform"]
        self.__update_interval = kwargs.get("update_interval", 0)
        self.__register_type = kwargs["register_type"]
        self.__entity_category = kwargs.get("entity_category", None)

        start_address = kwargs["start_address"]
        count = kwargs["count"]

        self.__start_id = kwargs.get("start_id", 0)
        self.__group_addresses = []
        self.__addresses = []
        self._register_statuses = [None] * count
        self.__last_date = 0

        self.add_addresses(0, start_address, count)

        if 'address0' in kwargs:
            self.add_addresses(0, kwargs["address0"], 1)
            self._register_statuses.append(None)
        # else:
        #     _LOGGER.debug(f"device.py; {self.name}. address0 НЕ НАЙДЕН!")

    @property
    def count(self):
        return len(self.__addresses)

    @property
    def entity_category(self):
        return self.__entity_category

    def get_channel(self, index: int) -> int | None:
        if self.count == 1:
            return None
        else:
            return self.start_id + index

    @property
    def device(self):
        return self.__device

    @property
    def name(self):
        return self.__name

    @property
    def name_id(self):
        return self.__name_id

    @property
    def platform(self):
        return self.__platform

    @property
    def register_type(self):
        return self.__register_type

    @property
    def start_id(self):
        return self.__start_id

    @property
    def update_interval(self):
        return self.__update_interval

    @property
    def group_addresses(self):
        return self.__group_addresses

    @property
    def addresses(self):
        return self.__addresses

    def address(self, index):
        return self.__addresses[index]

    @property
    def last_date(self):
        return self.__last_date

    def add_addresses(self, index:int, start_address:int, count:int):
        self.__group_addresses.insert(index, GroupAddresses(start_address, count))
        start_pos = index
        for i in range(count):
            self.__addresses.insert(start_pos + i, start_address + i)

    def get_state(self, index:int):
        return self._register_statuses[index]

    def _set_status(self, index, value):
        self._register_statuses[index] = value

    def update_statuses(self, list_value, group_addr):
        if isinstance(list_value, list):
            if len(list_value) == len(self._register_statuses):
                self._register_statuses = list_value
            elif len(list_value) < len(self._register_statuses):
                index = None
                try:
                    index = self.addresses.index(group_addr.start_address)
                except ValueError:
                    _LOGGER.warning(f"Не найден адрес '{group_addr.start_address}' в списке адресов '{self.addresses}"
                                    f"' объекта '{self.name}'")
                if not index is None:
                    self._register_statuses = self._register_statuses[:index] + list_value + self._register_statuses[index+group_addr.count:]
        self.__last_date = time.monotonic()

    async def set_value(self, index:int, value):
        self._register_statuses[index] = value
        await self.__device.set_register_value(
            self.__register_type,
            self.__addresses[index],
            value)

class SelectDeviceObjectGroup(DeviceObjectGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.__select_values = kwargs["select_values"]
        self.__select_values0 = kwargs.get("select_values0", self.__select_values)

    def get_state(self, index: int):
        # key = super().get_state(index)
        key = self._register_statuses[index]

        if key is None:
            return None

        if index == 0:
            return self.__select_values0[key]
        else:
            return self.__select_values[key]

    def get_attr_options(self, index:int):
        if index:
            return list(self.__select_values.values())
        else:
            return list(self.__select_values0.values())


    async def set_value(self, index:int, value):
        if index:
            dict_values = self.__select_values
        else:
            dict_values = self.__select_values0

        # Возвращает первый найденный ключ
        option_key = next((k for k, v in dict_values.items() if v == value), None)
        self._set_status(index, option_key)

        await self.device.set_register_value(self.register_type,self.address(index),option_key)

class WBSmart:
    def __init__(self, hass: HomeAssistant, host_ip: str, host_port: int, device_id: int) ->None:
        self.__name = ""
        self.__model = ""
        self.__firmware = ""
        self.__serial_number = ""
        self.__bootloader = ""
        self.__device_id = device_id
        self.__hass = hass
        self.objects = []

        # Флаг для отслеживания состояния подключения
        # TODO Добавить код увеличения попыток
        self.__connection_attempts = 0
        self.__is_connected = False

        self._hub = async_modbus_hub(hass=hass, host=host_ip, port=host_port)

        # asyncio.create_task(self.update_info())
        # try:
        #     # Get the running event loop
        #     loop = asyncio.get_running_loop()
        #     # Run the async function within the existing loop
        #     loop.run_until_complete(self.update_info())
        # except RuntimeError:
        #     # Handle cases where no loop is running (e.g., a simple script)
        #     asyncio.run(self.update_info())

        self.__name = f"{self.__model}_{self.__device_id}"

    # TODO реализовать вывод информации об устройстве "https://selectel.ru/blog/ha-karadio/" def device_info
    # @classmethod
    # async def create(cls, param):
    #     # Асинхронная инициализация
    #     await update_info()
    #     return cls(data)

    def __del__(self):
        self._hub.disconnect()
        _LOGGER.warning(f"Устройство {self.name} удалено. Отключено по Modbus")

    @property
    def model(self) -> str:
        return self.__model

    @property
    def firmware(self) -> str:
        return f"{self.__firmware} ({self.__bootloader})"

    @property
    def serial_number(self) -> str:
        return self.__serial_number

    @property
    def manufacturer(self) -> str:
        return "wirenboard"

    @property
    def name(self):
        return self.__name

    @property
    def device_id(self):
        return self.__device_id

    @property
    def is_connected(self):
        """Возвращает состояние подключения к устройству"""
        return self.__is_connected

    @property
    def connection_attempts(self):
        """Возвращает состояние подключения к устройству"""
        return self.__connection_attempts

    def connected(self):
        """Возвращает состояние подключения к устройству"""
        self.__is_connected = True

    def disconnected(self):
        """Возвращает состояние подключения к устройству"""
        self.__is_connected = False

    def inc_connection_attempts(self):
        self.__connection_attempts += 1

    def reset_connection_attempts(self):
        self.__connection_attempts = 0

    async def async_check_and_reconnect(self):
        """Проверяет подключение и пытается переподключиться при необходимости"""
        try:
            # Простая проверка - если клиент подключен, считаем что подключение есть
            if hasattr(self._hub, '_client') and self._hub._client.connected:
                self.connected()
                return True

            # Если не подключен, пытаемся подключиться
            _LOGGER.debug(f"Попытка подключения к устройству {self.__name}")
            await self._hub.connect()

            # Добавляем небольшую задержку после подключения для стабилизации
            await asyncio.sleep(0.2)

            self.connected()
            _LOGGER.debug(f"Успешно подключились к устройству {self.__name}")
            return True
        except Exception as e:
            _LOGGER.error(f"Не удалось подключиться к устройству {self.__name}: {e}")
            self.disconnected()
            return False

    async def write_coil_registers(self, address:int, values):
        try:
            async with async_timeout.timeout(5):
                _LOGGER.debug(f"Запись в coil регистры {address} устройства {self.device_id} значения {values}")
                await self._hub.async_write_coils(address, values, self.device_id)
        except TimeoutError:
            _LOGGER.warning("Pulling timed out")
            return False
        except ModbusException as value_error:
            _LOGGER.warning(f"Error write config register, modbus Exception {value_error.string}")
            return False
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exceptions")
            return False
        return True

    async def async_write_holding_register(self, address:int, value:int):
        try:
            async with async_timeout.timeout(5):
                _LOGGER.debug(f"Запись в holding регистр {address} устройства {self.device_id} значения {value}")
                await self._hub.async_write_holding_register(address, value, self.device_id)
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

    async def update_info(self):
        try:
            # Проверяем подключение
            connecting_status = await self.async_check_and_reconnect()
            # TODO Все warning в методе вернуть на debug
            # _LOGGER.debug(f"Metod update. connecting_status = {connecting_status}")
            if not connecting_status:
                _LOGGER.error(f"Не удалось подключиться к устройству {self.name}, пропускаем обновление")
                self.disconnected()
                return

            async with async_timeout.timeout(15):
                _LOGGER.info(f"Читаем с устройства {self.device_id} модель устройства")
                self.__model = await self._hub.async_read_holding_register_string(200, 20, self.device_id)
                self.__bootloader = await self._hub.async_read_holding_register_string(330, 7, self.device_id)
                self.__firmware = await self._hub.async_read_holding_register_string(250, 16, self.device_id)
                self.__serial_number = await self._hub.async_read_holding_register_uint32(270, 2, self.device_id)
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

    async def update(self):
        try:
            # Проверяем подключение
            connecting_status = await self.async_check_and_reconnect()
            # TODO Все warning в методе вернуть на debug
            # _LOGGER.debug(f"Metod update. connecting_status = {connecting_status}")
            if not connecting_status:
                _LOGGER.error(f"Не удалось подключиться к устройству {self.name}, пропускаем обновление")
                self.disconnected()
                return

            async with async_timeout.timeout(15):
                for obj in self.objects:
                    passed = time.monotonic() - obj.last_date
                    _LOGGER.debug(f"self.name={self.name}; obj.update_interval={obj.update_interval}; obj.last_date={obj.last_date}; passed={passed}")
                    if obj.register_type == RegisterType.holding:
                        _LOGGER.debug(f"obj.update_interval={obj.update_interval}; obj.last_date={obj.last_date}; passed={passed}")

                    if obj.update_interval == 0 and obj.last_date or obj.update_interval >= passed:
                        continue

                    match obj.register_type:
                        case RegisterType.coil:
                            for group_addr in obj.group_addresses:
                                _LOGGER.debug(f"Читаем с устройства {self.device_id} coil адреса {group_addr.start_address} регистров {group_addr.count}")
                                result = await self._hub.async_read_coils(group_addr.start_address, group_addr.count, self.device_id)
                                _LOGGER.debug(f"Из coil регистров получили ответ {result}")
                                # Проверяем, что данные получены корректно
                                if result is None:
                                    _LOGGER.error(f"Не удалось получить состояния {obj.name}")
                                    _LOGGER.warning(f"Читали с устройства {self.device_id} coil адреса {group_addr.start_address} регистров {group_addr.count}")
                                    self.disconnected()
                                    return
                                obj.update_statuses(result, group_addr)
                        case RegisterType.holding:
                            _LOGGER.debug(f"case RegisterType.holding 4")
                            for group_addr in obj.group_addresses:
                                _LOGGER.debug(f"Читаем с устройства {self.device_id} holding адреса {group_addr.start_address} регистров {group_addr.count}")
                                result = await self._hub.async_read_holding_register(group_addr.start_address, group_addr.count, self.device_id)
                                _LOGGER.debug(f"Из holding регистров получили ответ {result}")
                                # Проверяем, что данные получены корректно
                                if result is None:
                                    _LOGGER.error(f"Не удалось получить состояния {obj.name}")
                                    _LOGGER.warning(f"Читали с устройства {self.device_id} holding адреса {group_addr.start_address} регистров {group_addr.count}")
                                    self.disconnected()
                                    return
                                obj.update_statuses(result, group_addr)

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

    async def set_register_value(self, register_type:RegisterType, addr: int, value):
        _LOGGER.debug(f"set_register_value на входе register_type={register_type}; addr={addr}; value={value}")
        match register_type:
            case RegisterType.coil:
                result = await self.write_coil_registers(addr, [value])
            case RegisterType.holding:
                result = await self.async_write_holding_register(addr, value)
            case _:
                result = False

        _LOGGER.debug(f"set_register_value вернуло {result}")
        return result

    @property
    def switches(self):
        _LOGGER.debug("device.py switches шаг 1")
        switches = []
        for obj in self.objects:
            _LOGGER.debug(f"device.py switches шаг 2 obj={obj}")
            if obj.platform == Platform.switch:
                switches.append(obj)
                _LOGGER.debug(f"device.py switches шаг 3")
        return switches

    @property
    def selects(self):
        _LOGGER.debug("device.py selects шаг 1")
        selects = []
        for obj in self.objects:
            _LOGGER.debug(f"device.py selects шаг 2 obj={obj}")
            if obj.platform == Platform.select:
                selects.append(obj)
                _LOGGER.debug(f"device.py switches шаг 3")
        return selects

    @property
    def sensors(self):
        _LOGGER.debug("device.py selects шаг 1")
        selects = []
        for obj in self.objects:
            _LOGGER.debug(f"device.py selects шаг 2 obj={obj}")
            if obj.platform == Platform.sensor:
                selects.append(obj)
                _LOGGER.debug(f"device.py switches шаг 3")
        return selects

class WBMr(WBSmart):
    def __init__(self, hass: HomeAssistant, host_ip: str, host_port: int, device_id: int) -> None:

        super().__init__(hass, host_ip, host_port, device_id)
        # Инициализируем атрибуты, которые используются в update()
        self.objects = [
            DeviceObjectGroup(device=self,
                                name="Реле",
                                # name_id="switch",
                                start_id=1,
                                platform=Platform.switch,
                                register_type=RegisterType.coil,
                                start_address=0,
                                count=6,
                                update_interval=1),
            SelectDeviceObjectGroup(device=self,
                                    name="Режим работы входа",
                                    name_id="input_mode",
                                    platform=Platform.select,
                                    register_type=RegisterType.holding,
                                    start_address=9,
                                    count=6,
                                    select_values=INPUT_MODE_VALUES,
                                    select_values0=INPUT_MODE_VALUES_0,
                                    address0=16,
                                    entity_category=EntityCategory.CONFIG),
            SelectDeviceObjectGroup(device=self,
                                    name="Состояния выходов при подаче питания",
                                    name_id="status_outputs_when_power_applied",
                                    platform=Platform.select,
                                    register_type=RegisterType.holding,
                                    start_address=6,
                                    count=1,
                                    # update_interval=5,
                                    select_values=STATUS_OUTPUTS_WHEN_POWER_APPLIED,
                                    entity_category=EntityCategory.CONFIG),
            DeviceObjectGroup(device=self,
                              name="Счетчик срабатываний входа",
                              name_id="trigger_counter",
                              platform=Platform.sensor,
                              register_type=RegisterType.holding,
                              start_address=32,
                              count=6,
                              address0=39,
                              update_interval=1),
        ]

        # _LOGGER.debug(f"device.py WBMr __init__ self.objects={self.objects}")

        # Счетчик срабатываний входа

        # Счётчик коротких нажатий

        # Счётчик длинных нажатий

        # Счётчик двойных нажатий

        # Счётчик короткого, а затем длинного нажатий

        # Регистры mapping-матрицы

        # Регистры mapping-матрицы для коротких нажатий

        # Регистры mapping-матрицы для длинных нажатий

        # Регистры mapping-матрицы для двойных нажатий

        # Регистры mapping-матрицы для сначала короткого, потом длинного нажатий

        # Регистры mapping-матрицы для размыкания кнопки

        # Регистры mapping-матрицы для замыкания кнопки

        # Время подавления дребезга [мс]

        # Время длинного нажатия [мс]

        # Время ожидания второго нажатия [мс]

        # Задержка включения (x0.1, с)

        # Задержка повторного включения (x0.1, с)

