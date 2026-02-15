from __future__ import annotations

import time
import logging
from dataclasses import field

import async_timeout

from enum import Enum
from asyncio.exceptions import InvalidStateError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from pymodbus import ModbusException
from pymodbus.exceptions import ModbusIOException
from .const import (
    MR_INPUT_MODE,
    MR_INPUT_MODE_0,
    MR_STATUS_OUTPUTS_WHEN_POWER_APPLIED,
    MSM_INPUT_MODE
)

_LOGGER = logging.getLogger(__name__)

class Platform(Enum):
    # binary_sensor = "bs"
    sensor = "sn"
    select = "se"
    switch = "sw"
    number = "nu"
    # light = "li"

class RegisterType(Enum):
    coil = 1
    holding = 2
    discrete_input = 3

class Model(Enum):
    wbmr6c_v2 = "WB-MR6C v.2"
    wbmr6c_v3 = "WB-MR6C v.3"
    wbmio = "WB-MGE v.3"
    wbmd3 = "WB-MDM3"
    wb_led = "WB-LED"
    wbmcm8 = "WB-MCM8"

class FieldFormat(Enum):
    BOOL = "bool"
    U16 = "int16"
    U32 = "int32"


class GroupAddresses:
    def __init__(self, start_address: int, count: int):
        self.start_address = start_address
        self.count = count

class DeviceObjectsGroup:
    def __init__(self, **kwargs):
        self.__device = kwargs["device"]
        self.__name = kwargs["name"]
        self.__name_id = kwargs.get("name_id", "")
        self.__platform = kwargs["platform"]
        self.__update_interval = kwargs.get("update_interval", 0)
        self.__entity_category = kwargs.get("entity_category", None)

        self.__start_id = kwargs.get("start_id", 0)
        self.__addresses_group = kwargs["addresses_group"]
        self.__last_date = 0

        self.__entity_values = []

        for address_group in self.__addresses_group:
            values = [None] * address_group["count"]

            slave_values = {}
            for slave in address_group.get("slaves", []):
                slave_values[slave["name"]] = values

            self.add_group_states(self.__entity_values, address_group, values, slave_values)

    def get_component_values(self, address_group, start_index):
        result = []
        count = address_group["count"]
        device_info = self.device.device_info
        for i in range(count):
            index = start_index + i

            addresses = {
                "base": {
                    "address": address_group["start_address"] + i,
                    "type": address_group["type"]
                }
            }

            select_values = address_group.get("select_values")
            if not select_values is None:
                addresses["base"]["select_values"] = select_values

            for slave in address_group.get("slaves", []):
                addresses[slave["name"]] = {
                    "address": slave["start_address"] + i,
                    "type": slave["type"]
                }
                select_values = slave.get("select_values")
                if not select_values is None:
                    addresses[slave["name"]]["select_values"] = select_values

            entity_value = {
                "object": self,
                "object_name": self.name,
                "object_name_id": self.name_id,
                "entity_category": self.entity_category,
                "channel": self.get_channel(index),
                "addresses": addresses,
                "id": index,
                "platform_name": self.platform.name,
                "device_info": device_info
            }

            result.append(entity_value)

        return start_index + count, result

    # @property
    # def count(self):
    #     return len(self.__entity_values)

    @property
    def entity_category(self):
        return self.__entity_category

    def get_channel(self, index: int) -> int:
        return self.__start_id + index

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
    def update_interval(self):
        return self.__update_interval

    @property
    def addresses_group(self):
        return self.__addresses_group

    @property
    def last_date(self):
        return self.__last_date

    def update_last_date(self):
        self.__last_date = time.monotonic()

    def get_state(self, index:int):
        # {'base': None, 'brightness': None}
        return self.__entity_values[index]["base"]

    @property
    def entity_values(self):
         return self.__entity_values

    def update_statuses(self, entity_values:list):
        self.__entity_values = entity_values
        self.update_last_date()

    def add_group_states(self, entity_values:list, addr_group:dict,
                         base_states:list, slave_states:dict):
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
            state = {"base":base_states[i]}
            for key, value in slave_states.items():
                state[key] = value[i]

            entity_values.append(state)

        # На выходе получаем:
        # entity_values = [{"base":True, "brightness":50}, {"base":False, "brightness":70}, {"base":False, "brightness":20}]

    async def set_value(self, entity_addresses, entity_id, value_name, value):
        match entity_addresses[value_name]["type"]:
            case FieldFormat.U16:
                _value = int(value)
            case FieldFormat.U32:
                _value = int(value)
            case FieldFormat.BOOL:
                _value = bool(value)
            case _:
                _value = int(value)

        # _LOGGER.debug(f"Записываем value={_value}; type={type(_value)}")

        self.__entity_values[entity_id][value_name] = _value
        await self.__device.set_register_value(
            entity_addresses[value_name]["type"],
            entity_addresses[value_name]["address"],
            _value
        )

class SwitchDeviceObjectsGroup(DeviceObjectsGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class LightDeviceObjectsGroup(DeviceObjectsGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class SensorDeviceObjectsGroup(DeviceObjectsGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class SelectDeviceObjectsGroup(DeviceObjectsGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class InputDeviceObjectsGroup(DeviceObjectsGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__min_val = kwargs["min_val"]
        self.__max_val = kwargs["max_val"]
        self.__mode = kwargs["mode"]
        self.__step = kwargs["step"]
        self.__scale = kwargs["scale"]

    def get_component_values(self, address_group, start_index):
        index, components_values = super().get_component_values(address_group, start_index)

        for values in components_values:
            values["min_val"] = self.__min_val
            values["max_val"] = self.__max_val
            values["mode"] = self.__mode
            values["step"] = self.__step
            values["scale"] = self.__scale

        return index, components_values

class WBSmart:
    def __init__(self, hass: HomeAssistant, coordinator, host_ip: str, host_port: int, device_id: int, model:Model) ->None:
        self.__hass = hass
        self.__coordinator = coordinator
        self.__model = model
        self.__firmware = ""
        self.__serial_number = ""
        self.__bootloader = ""
        self.__host_ip = host_ip
        self.__host_port = host_port
        self.__device_id = device_id
        self.__is_connected = False
        self.objects = []

        self.__name = f"{self.__model.name}_{self.__device_id}"

    def __del__(self):
        _LOGGER.warning(f"Устройство {self.name} удалено.")

    @property
    def coordinator(self) :
        return self.__coordinator

    @property
    def host_ip(self) -> str:
        return self.__host_ip

    @property
    def host_port(self) -> int:
        return self.__host_port

    @property
    def model(self) -> Model:
        return self.__model

    @property
    def sw_version(self) -> str:
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
    def connected(self):
        return self.__is_connected

    @connected.setter
    def connected(self, value: bool):
        self.__is_connected = value

    @property
    def device_info(self):
        return {
            "device": self,
            "name": self.name,
            "serial_number": self.serial_number,
            "model": self.model,
            "device_id": self.device_id,
            "sw_version": self.sw_version,
            "manufacturer": self.manufacturer,
        }

    async def init_update(self, hub):
        try:
            async with async_timeout.timeout(15):
                model = await hub.async_read_holding_string(200, 20, self.device_id)
                self.__model = model.replace("-", "_").lower()
                self.__bootloader = await hub.async_read_holding_string(330, 7, self.device_id)
                self.__firmware = await hub.async_read_holding_string(250, 16, self.device_id)
                self.__serial_number = await hub.async_read_holding_uint32(270, 2, self.device_id)
                self.__name = f"{self.__model}_{self.__device_id}"

                _LOGGER.info(f"model={self.__model}; bootloader={self.__bootloader}; firmware={self.__firmware}; "
                             f"S/N={self.__serial_number}")
                # Если данные получены успешно, считаем что подключение активно
                self.connected = True
        except TimeoutError:
            _LOGGER.warning(f"Polling timed out for {self.name} - устройство не отвечает")
            self.connected = False
            return
        except ModbusIOException as value_error:
            _LOGGER.warning(f"ModbusIOException for {self.name}: {value_error.string}")
            self.connected = False
            return
        except ModbusException as value_error:
            _LOGGER.warning(f"ModbusException for {self.name}: {value_error.string}")
            self.connected = False
            return
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exceptions for {self.name}")
            self.connected = False
            return
        except Exception as e:
            _LOGGER.error(f"Неожиданная ошибка при обновлении {self.name}: {e}")
            self.connected = False
            return

    async def read_address_group(self, hub, addr_group):
        count: int = addr_group["count"]
        start_address: int = addr_group["start_address"]
        register_type: RegisterType = addr_group["type"]

        async_read_registers = None
        result = [None]*count
        response = None

        def_name = ""
        match register_type:
            case RegisterType.coil:
                async_read_registers = hub.async_read_coils
            case RegisterType.holding:
                if addr_group["field_format"] == FieldFormat.U32:
                    count *= 2
                    async_read_registers = hub.async_read_holding_uint32
                    # nonlocal def_name
                    def_name = "async_read_holding_uint32"
                else:
                    async_read_registers = hub.async_read_holding
                    # nonlocal def_name
                    def_name = "async_read_holding"
            case RegisterType.discrete_input:
                async_read_registers = hub.async_read_discrete_inputs
            case _:
                _LOGGER.warning(f"Не нашли действия для  '{register_type.name}'")

        if async_read_registers is None:
            self.connected = False
            return result

        _LOGGER.debug(
            f"def_name='{def_name}'. Читаем с {self.device_id} '{register_type.name}' {count} регистров, начиная с адреса {start_address}")

        try:
            async with async_timeout.timeout(15):
                response = await async_read_registers(start_address, count, self.device_id)
                _LOGGER.debug(f"Из '{register_type.name}' регистров получили ответ {response}")
        except TimeoutError:
            _LOGGER.warning(f"Polling timed out for {self.name} - устройство не отвечает")
            response = None
        except ModbusIOException as value_error:
            _LOGGER.warning(f"ModbusIOException for {self.name}: {value_error.string}")
            response = None
        except ModbusException as value_error:
            _LOGGER.warning(f"ModbusException for {self.name}: {value_error.string}")
            response = None
        except InvalidStateError as ex:
            _LOGGER.error(f"InvalidStateError Exceptions for {self.name}")
            response = None
        except Exception as e:
            _LOGGER.error(f"Неожиданная ошибка при обновлении {self.name}: {e}")
            response = None

        # Проверяем, что данные получены корректно
        if response is None:
            _LOGGER.warning(
                f"С устройства {self.device_id}, начиная с '{start_address}' адреса, "
                f"не удалось прочитать {count} регистров '{register_type.name}'")
            self.connected = False
        else:
            result = response

            # Если данные получены успешно, считаем что подключение активно
            self.connected = True

        return result

    async def update(self, hub):
        for obj in self.objects:
            entity_values = []
            passed = time.monotonic() - obj.last_date
            _LOGGER.debug(f"self.name={self.name}; obj.update_interval={obj.update_interval}; "
                          f"obj.last_date={obj.last_date}; passed={passed}")

            if obj.update_interval == 0 and obj.last_date or obj.update_interval >= passed:
                continue

            for addr_group in obj.addresses_group:
                response = await self.read_address_group(hub, addr_group)
                slave_values = {}
                for slave in addr_group.get("slaves", []):
                    slave_response = await self.read_address_group(hub, slave)
                    slave_values[slave["name"]] = slave_response

                # slave_states = {"brightness":[50,70,20]}
                obj.add_group_states(entity_values, addr_group, response, slave_values)

            obj.update_statuses(entity_values)

    async def set_register_value(self, register_type:RegisterType, address: int, value):
        self.connected = await self.coordinator.set_register_value(
            self.host_ip,
            self.host_port,
            self.device_id,
            register_type,
            address,
            value
        )

    def get_objects(self, platform:Platform | None = None) -> list:
        _LOGGER.debug("device.py get_objects_group шаг 1")
        result = []
        if platform is None:
            return self.objects.copy()
        else:
            for obj in self.objects:
                _LOGGER.debug(f"device.py get_objects_group шаг 2 obj={obj}")
                if obj.platform == platform:
                    result.append(obj)
                    _LOGGER.debug(f"device.py get_objects_group шаг 3")
            return result


class WBMR6C(WBSmart):
    def __init__(self, hass: HomeAssistant, coordinator, host_ip: str, host_port: int, device_id: int, model:Model) -> None:

        super().__init__(hass, coordinator, host_ip, host_port, device_id, model)
        # Инициализируем атрибуты, которые используются в update()
        self.objects = [
            SwitchDeviceObjectsGroup(
                device=self,
                name="Реле",
                # name_id="switch",
                start_id=1,
                platform=Platform.switch,
                addresses_group=[
                    {"type":RegisterType.coil,"start_address":0, "count":6, "field_format":FieldFormat.BOOL},
                ],
                update_interval=0.1
            ),
            SelectDeviceObjectsGroup(
                device=self,
                name="Режим входа",
                name_id="input_mode",
                platform=Platform.select,
                addresses_group=[
                    {"type":RegisterType.holding, "start_address":16, "count":1, "field_format":FieldFormat.U16,
                     "select_values":MR_INPUT_MODE_0},
                    {"type":RegisterType.holding, "start_address":9, "count":6, "field_format":FieldFormat.U16,
                     "select_values":MR_INPUT_MODE},
                ],
                entity_category=EntityCategory.CONFIG
            ),
            SelectDeviceObjectsGroup(
                device=self,
                name="Состояния выходов при подаче питания",
                name_id="status_outputs_when_power_applied",
                platform=Platform.select,
                addresses_group=[
                    {"type":RegisterType.holding,"start_address":6, "count":1, "field_format":FieldFormat.U16,
                     "select_values":MR_STATUS_OUTPUTS_WHEN_POWER_APPLIED},
                ],
                entity_category=EntityCategory.CONFIG
            ),
            # SensorDeviceObjectsGroup(
            #     device=self,
            #     name="Счетчик срабатываний входа",
            #     name_id="counter",
            #     platform=Platform.sensor,
            #     addresses_group=[
            #         {"type":RegisterType.holding, "start_address":39, "count":1, "field_format":FieldFormat.U16},
            #         {"type":RegisterType.holding, "start_address":32, "count":6, "field_format":FieldFormat.U16},
            #     ],
            #     entity_category=EntityCategory.DIAGNOSTIC,
            #     update_interval=1
            # ),
            # SensorDeviceObjectsGroup(
            #     device=self,
            #     name="Счётчик коротких нажатий",
            #     name_id="short_click_counter",
            #     platform=Platform.sensor,
            #     addresses_group=[
            #         {"type":RegisterType.holding, "start_address":471, "count":1, "field_format":FieldFormat.U16},
            #         {"type":RegisterType.holding, "start_address":464, "count":6, "field_format":FieldFormat.U16},
            #     ],
            #     entity_category=EntityCategory.DIAGNOSTIC,
            #     update_interval=1,
            # ),
            # SensorDeviceObjectsGroup(
            #     device=self,
            #     name="Счётчик длинных нажатий",
            #     name_id="long_click_counter",
            #     platform=Platform.sensor,
            #     addresses_group=[
            #         {"type":RegisterType.holding, "start_address":487, "count":1, "field_format":FieldFormat.U16},
            #         {"type":RegisterType.holding, "start_address":480, "count":6, "field_format":FieldFormat.U16},
            #     ],
            #     entity_category=EntityCategory.DIAGNOSTIC,
            #     update_interval=1,
            # ),
            # SensorDeviceObjectsGroup(
            #     device=self,
            #     name="Счётчик двойных нажатий",
            #     name_id="double_click_counter",
            #     platform=Platform.sensor,
            #     addresses_group=[
            #         {"type":RegisterType.holding, "start_address":503, "count":1, "field_format":FieldFormat.U16},
            #         {"type":RegisterType.holding, "start_address":496, "count":6, "field_format":FieldFormat.U16},
            #     ],
            #     entity_category=EntityCategory.DIAGNOSTIC,
            #     update_interval=1,
            # ),
            # SensorDeviceObjectsGroup(
            #     device=self,
            #     name="Счётчик короткого, а затем длинного нажатий",
            #     name_id="short_long_click_counter",
            #     platform=Platform.sensor,
            #     addresses_group=[
            #         {"type":RegisterType.holding, "start_address":519, "count":1, "field_format":FieldFormat.U16},
            #         {"type":RegisterType.holding, "start_address":512, "count":6, "field_format":FieldFormat.U16},
            #     ],
            #     entity_category=EntityCategory.DIAGNOSTIC,
            #     update_interval=1,
            # ),
            # InputDeviceObjectsGroup(
            #     device=self,
            #     name="Время подавления дребезга",
            #     name_id="debounce_time",
            #     platform=Platform.number,
            #     min_val=0,
            #     max_val=2000,
            #     mode="box",  # box or slider
            #     step=1,
            #     scale=1,
            #     entity_category=EntityCategory.CONFIG,
            #     addresses_group=[
            #         {"type":RegisterType.holding, "start_address":27, "count":1, "field_format":FieldFormat.U16},
            #         {"type":RegisterType.holding, "start_address":20, "count":6, "field_format":FieldFormat.U16},
            #     ],
            # ),
            # InputDeviceObjectsGroup(
            #     device=self,
            #     name="Время длинного нажатия",
            #     name_id="long_click_time",
            #     platform=Platform.number,
            #     min_val=500,
            #     max_val=5000,
            #     mode="slider",  # box or slider
            #     step=50,
            #     scale=1,
            #     entity_category=EntityCategory.CONFIG,
            #     addresses_group=[
            #         {"type":RegisterType.holding, "start_address":1107, "count":1, "field_format":FieldFormat.U16},
            #         {"type":RegisterType.holding, "start_address":1100, "count":6, "field_format":FieldFormat.U16},
            #     ],
            # ),
            # InputDeviceObjectsGroup(
            #     device=self,
            #     name="Время ожидания второго нажатия",
            #     name_id="second_click_timeout",
            #     platform=Platform.number,
            #     min_val=0,
            #     max_val=2000,
            #     mode="slider",  # box or slider
            #     step=50,
            #     scale=1,
            #     entity_category=EntityCategory.CONFIG,
            #     addresses_group=[
            #         {"type":RegisterType.holding, "start_address":1147, "count":1, "field_format":FieldFormat.U16},
            #         {"type":RegisterType.holding, "start_address":1140, "count":6, "field_format":FieldFormat.U16},
            #     ],
            # ),
        ]

class WBMCM8(WBSmart):
    def __init__(self, hass: HomeAssistant, coordinator, host_ip: str, host_port: int, device_id: int, model:Model) -> None:

        super().__init__(hass, coordinator, host_ip, host_port, device_id, model)
        # Инициализируем атрибуты, которые используются в update()
        self.objects = [
            SensorDeviceObjectsGroup(
                device=self,
                name="Состояние входа",
                name_id="input_status",
                start_id=1,
                platform=Platform.sensor,
                addresses_group=[
                    {"type":RegisterType.discrete_input, "start_address":0, "count":8, "field_format":FieldFormat.BOOL},
                ],
                update_interval=0.1
            ),
            # SensorDeviceObjectsGroup(
            #     device=self,
            #     name="Счетчик срабатываний входа",
            #     name_id="counter",
            #     start_id=1,
            #     platform=Platform.sensor,
            #     addresses_group=[
            #         {"type":RegisterType.holding, "start_address":60, "count":8, "field_format":FieldFormat.U32},
            #     ],
            #     entity_category=EntityCategory.DIAGNOSTIC,
            #     update_interval=1
            # ),
            # SensorDeviceObjectsGroup(
            #     device=self,
            #     name="Счётчик коротких нажатий",
            #     name_id="short_click_counter",
            #     start_id=1,
            #     platform=Platform.sensor,
            #     addresses_group=[
            #         {"type":RegisterType.holding, "start_address":464, "count":8, "field_format":FieldFormat.U16},
            #     ],
            #     entity_category=EntityCategory.DIAGNOSTIC,
            #     update_interval=1,
            # ),
            # SensorDeviceObjectsGroup(
            #     device=self,
            #     name="Счётчик длинных нажатий",
            #     name_id="long_click_counter",
            #     start_id=1,
            #     platform=Platform.sensor,
            #     addresses_group=[
            #         {"type":RegisterType.holding, "start_address":480, "count":8, "field_format":FieldFormat.U16},
            #     ],
            #     entity_category=EntityCategory.DIAGNOSTIC,
            #     update_interval=1,
            # ),
            # SensorDeviceObjectsGroup(
            #     device=self,
            #     name="Счётчик двойных нажатий",
            #     name_id="double_click_counter",
            #     start_id=1,
            #     platform=Platform.sensor,
            #     addresses_group=[
            #         {"type":RegisterType.holding, "start_address":496, "count":8, "field_format":FieldFormat.U16},
            #     ],
            #     entity_category=EntityCategory.DIAGNOSTIC,
            #     update_interval=1,
            # ),
            # SensorDeviceObjectsGroup(
            #     device=self,
            #     name="Счётчик короткого, а затем длинного нажатий",
            #     name_id="short_long_click_counter",
            #     start_id=1,
            #     platform=Platform.sensor,
            #     addresses_group=[
            #         {"type":RegisterType.holding, "start_address":512, "count":8, "field_format":FieldFormat.U16},
            #     ],
            #     entity_category=EntityCategory.DIAGNOSTIC,
            #     update_interval=1,
            # ),
            SelectDeviceObjectsGroup(device=self,
                name="Режим входа",
                name_id="input_mode",
                start_id=1,
                platform=Platform.select,
                addresses_group=[
                    {"type":RegisterType.holding, "start_address":9, "count":8, "field_format":FieldFormat.U16,
                     "select_values":MSM_INPUT_MODE},
                ],
                entity_category=EntityCategory.CONFIG
            ),
            InputDeviceObjectsGroup(
                device=self,
                name="Время подавления дребезга",
                name_id="debounce_time",
                start_id=1,
                platform=Platform.number,
                min_val=0,
                max_val=100,
                mode="box",  # box or slider
                step=1,
                scale=1,
                entity_category=EntityCategory.CONFIG,
                addresses_group=[
                    {"type":RegisterType.holding, "start_address":20, "count":8, "field_format":FieldFormat.U16},
                ],
            ),
            InputDeviceObjectsGroup(
                device=self,
                name="Время длинного нажатия",
                name_id="long_click_time",
                start_id=1,
                platform=Platform.number,
                min_val=500,
                max_val=5000,
                mode="slider",  # box or slider
                step=50,
                scale=1,
                entity_category=EntityCategory.CONFIG,
                addresses_group=[
                    {"type":RegisterType.holding, "start_address":1100, "count":8, "field_format":FieldFormat.U16},
                ],
            ),
            InputDeviceObjectsGroup(
                device=self,
                name="Время ожидания второго нажатия",
                name_id="second_click_timeout",
                start_id=1,
                platform=Platform.number,
                min_val=0,
                max_val=2000,
                mode="slider",  # box or slider
                step=50,
                scale=1,
                entity_category=EntityCategory.CONFIG,
                addresses_group=[
                    {"type":RegisterType.holding, "start_address":1140, "count":8, "field_format":FieldFormat.U16},
                ],
            ),
        ]

class WBMDM3(WBSmart):
    def __init__(self, hass: HomeAssistant, coordinator, host_ip: str, host_port: int, device_id: int, model:Model) -> None:

        super().__init__(hass, coordinator, host_ip, host_port, device_id, model)
        # Инициализируем атрибуты, которые используются в update()
        self.objects = [
            LightDeviceObjectsGroup(
                device=self,
                name="Лампа",
                start_id=1,
                platform=Platform.light,
                addresses_group=[
                    {"type":RegisterType.coil,"start_address":0,"count":3,"field_format":FieldFormat.U16,
                        "slaves":[
                            {"name":"brightness","type":RegisterType.holding, "start_address":0, "count":3,"field_format":FieldFormat.U16},
                        ]
                    }
                ],
                update_interval=0.1
            ),
        ]


# 2026-02-13 06:21:32.254 WARNING (MainThread) [custom_components.wirenboard.hub] Error write config register, modbus Exception [Input/Output] No response received after 5 retries, continue with next request
# 2026-02-13 06:21:33.740 WARNING (MainThread) [custom_components.wirenboard.device] Polling timed out for wbmcm8_69 - устройство не отвечает
# 2026-02-13 06:21:49.741 WARNING (MainThread) [custom_components.wirenboard.device] Polling timed out for wbmr6c_116 - устройство не отвечает
# 2026-02-13 06:22:04.745 WARNING (MainThread) [custom_components.wirenboard.device] Polling timed out for wbmcm8_69 - устройство не отвечает
# 2026-02-13 06:22:20.739 WARNING (MainThread) [custom_components.wirenboard.device] Polling timed out for wbmr6c_116 - устройство не отвечает
# 2026-02-13 06:22:32.262 ERROR (MainThread) [pymodbus.logging] No response received after 5 retries, continue with next request
# >>>>> send: 0x0 0x18 0x0 0x0 0x0 0x8 0x74 0xf 0x0 0x1 0x0 0x1 0x1 0x1
# >>>>> send: 0x0 0x18 0x0 0x0 0x0 0x8 0x74 0xf 0x0 0x1 0x0 0x8 0x1 0x1
# >>>>> Repeating....
# >>>>> send: 0x0 0x18 0x0 0x0 0x0 0x8 0x74 0xf 0x0 0x1 0x0 0x8 0x1 0x1
# >>>>> send: 0x0 0x18 0x0 0x0 0x0 0x8 0x74 0xf 0x0 0x1 0x0 0x8 0x1 0x1
# >>>>> send: 0x0 0x18 0x0 0x0 0x0 0x8 0x74 0xf 0x0 0x1 0x0 0x8 0x1 0x1
# 2026-02-13 06:22:32.262 WARNING (MainThread) [custom_components.wirenboard.hub] Error write config register, modbus Exception [Input/Output] No response received after 5 retries, continue with next request
# 2026-02-13 06:22:35.741 ERROR (MainThread) [custom_components.wirenboard.device] Не удалось получить состояния Состояние входа
# 2026-02-13 06:22:35.741 WARNING (MainThread) [custom_components.wirenboard.device] Читали с устройства 69 holding адреса 0 регистров 8
# 2026-02-13 06:22:51.740 ERROR (MainThread) [custom_components.wirenboard.device] Не удалось получить состояния Реле
# 2026-02-13 06:22:51.741 WARNING (MainThread) [custom_components.wirenboard.device] Читали с устройства 116 coil адреса 0 регистров 6