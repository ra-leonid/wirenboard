
from __future__ import annotations

import re
import asyncio
import logging
from typing import Any, Dict, List, Optional

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow, ConfigFlowResult
from homeassistant.core import callback
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_NAME,
)

from .hub import async_modbus_hub
from .device import Model
from .const import (
    DOMAIN,
    DEFAULT_IP,
    DEFAULT_PORT1,
    DEFAULT_PORT2,
    CONF_SLAVE_IDS_PORT1,
    CONF_SLAVE_IDS_PORT2,
    DEFAULT_SLAVE_IDS_PORT1,
    DEFAULT_SLAVE_IDS_PORT2,
    CONF_PORT1,
    CONF_PORT2,
    CONF_DEVICES,
)

_LOGGER = logging.getLogger(__name__)

# Глобальный словарь для хранения задач сканирования
_SCANNING_TASKS: Dict[str, asyncio.Task] = {}

async def async_validate_device(port, address: str | None, device_id:int) -> None:
    # Простая валидация - считаем что устройство доступно
    # Детальная проверка будет происходить при инициализации интеграции
    # TODO Реализовать проверку заполнения свойств
    pass


class WBSmartConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Wirenboard with WB-MGE v.3."""

    data: Optional[dict(str, Any)]

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._host: str | None = None
        self._ip: str | None = None
        self._port1: int | None = None
        self._port2: int | None = None
        self._ids_port1: List[int] = []
        self._ids_port2: List[int] = []
        self._discovered_devices: List[Dict[str, Any]] = []
        self._scan_error: Exception | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Invoke when a user initiates a flow via the user interface."""
        _LOGGER.debug(f"ЗАШЛИ async_step_user. CONF_HOST={CONF_HOST}")
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port1 = user_input[CONF_PORT1]
            self._port2 = user_input[CONF_PORT2]
            self._ids_port1 = list(map(int, re.findall(r'\d+', user_input[CONF_SLAVE_IDS_PORT1])))
            self._ids_port2 = list(map(int, re.findall(r'\d+', user_input[CONF_SLAVE_IDS_PORT2])))

            _LOGGER.debug(f"_ids_port1={self._ids_port1}")
            _LOGGER.debug(f"_ids_port2={self._ids_port2}")

            _LOGGER.debug(f"_port1={self._port1}")
            _LOGGER.debug(f"_port2={self._port2}")

            _LOGGER.debug(f"user_input[CONF_SLAVE_IDS_PORT1]={user_input[CONF_SLAVE_IDS_PORT1]}")
            _LOGGER.debug(f"user_input[CONF_SLAVE_IDS_PORT2]={user_input[CONF_SLAVE_IDS_PORT2]}")

            # Переходим к сканированию
            return await self.async_step_scan()

        data_schema = vol.Schema({
            vol.Required(CONF_HOST, default=DEFAULT_IP): cv.string,
            vol.Required(CONF_PORT1, default=DEFAULT_PORT1): cv.port,
            vol.Required(CONF_PORT2, default=DEFAULT_PORT2): cv.port,
            vol.Required(CONF_SLAVE_IDS_PORT1, default=DEFAULT_SLAVE_IDS_PORT1): cv.string,
            vol.Required(CONF_SLAVE_IDS_PORT2, default=DEFAULT_SLAVE_IDS_PORT2): cv.string,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
        # return await self.async_step_tcp(user_input)

    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        _LOGGER.debug("ЗАШЛИ async_step_scan")
        """Handle the scanning step."""
        if user_input is None:
            _LOGGER.debug("async_step_scan; if user_input is None")
            # Здесь выводится пустая форма сканирования
            return self.async_show_form(
                step_id="scan",
                description_placeholders={
                    "host": self._host,
                    "port1": self._port1,
                    "port2": self._port2,
                    "ids_port1": self._ids_port1,
                    "ids_port2": self._ids_port2,
                },
                data_schema=vol.Schema({}),
            )

        # Создаем и запускаем задачу сканирования
        _LOGGER.debug("async_step_scan; Создаем и запускаем задачу сканирования")
        scanning_task = self.hass.async_create_task(
            self._scan_devices()
        )

        # Сохраняем задачу в глобальном словаре
        _LOGGER.debug("async_step_scan; Сохраняем задачу в глобальном словаре")
        _SCANNING_TASKS[self.flow_id] = scanning_task

        # Показываем прогресс
        _LOGGER.debug("async_step_scan; Показываем прогресс")
        return self.async_show_progress(
            step_id="scan_progress",
            progress_action="scanning",
            progress_task=scanning_task,
            description_placeholders={
                "host": self._host,
                "port1": self._port1,
                "port2": self._port2,
                "ids_port1": self._ids_port1,
                "ids_port2": self._ids_port2,
            },
        )

    async def async_step_scan_progress(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        _LOGGER.debug("ЗАШЛИ async_step_scan_progress")
        """Handle the result of scanning progress."""

        # Получаем задачу из глобального словаря
        scanning_task = _SCANNING_TASKS.get(self.flow_id)

        if scanning_task is None:
            _LOGGER.error("Scanning task not found for flow %s", self.flow_id)
            return self.async_abort(reason="scan_task_not_found")

        # Проверяем, завершена ли задача
        if scanning_task.done():
            try:
                # Получаем результат задачи
                await scanning_task
                # Успех
                _LOGGER.debug("async_step_scan_progress. Задача выполнена успешно")
                self._scan_error = None
            except Exception as ex:
                # Ошибка
                self._scan_error = ex
                _LOGGER.error("Scanning failed: %s", ex, exc_info=True)
            finally:
                # Удаляем задачу из глобального словаря
                _SCANNING_TASKS.pop(self.flow_id, None)

            # Всегда переходим к выбору устройств после завершения прогресса
            _LOGGER.debug("async_step_scan_progress. Всегда переходим к выбору устройств после завершения прогресса")
            return self.async_show_progress_done(next_step_id="select_devices")

        # Если задача еще не завершена, продолжаем ждать
        _LOGGER.debug("async_step_scan_progress. Задача еще не завершена, продолжаем ждать")
        return self.async_show_progress_done(next_step_id="scan_progress")

    async def _scan_devices(self) -> None:
        """Scan for devices on both ports."""
        _LOGGER.debug("ЗАШЛИ _scan_devices")
        self._discovered_devices = []

        try:
            # Сканируем порты
            _LOGGER.info(f"Начинаем сканирование порта {self._port1}")
            devices_port1 = await self._scan_port(self._host, self._port1, self._ids_port1)
            self._discovered_devices.extend(devices_port1)

            _LOGGER.info(f"Начинаем сканирование порта {self._port2}")
            devices_port2 = await self._scan_port(self._host, self._port2, self._ids_port2)
            self._discovered_devices.extend(devices_port2)

            _LOGGER.info(
                "Найдено %d устройств на %s:%s и %s:%s",
                len(self._discovered_devices),
                self._host, self._port1,
                self._host, self._port2,
            )

            # Выводим список найденных устройств
            for i, device in enumerate(self._discovered_devices, 1):
                _LOGGER.info(f"Устройство {i}: {device['model']} на slave_id={device['slave_id']}")

        except Exception as ex:
            _LOGGER.error("Ошибка сканирования устройств: %s", ex, exc_info=True)
            raise

    async def async_check_and_reconnect(self, hub:async_modbus_hub) -> bool:
        """Проверяет подключение и пытается переподключиться при необходимости"""
        try:
            # Простая проверка - если клиент подключен, считаем что подключение есть
            if hasattr(hub, '_client') and hub._client.connected:
                return True

            # Если не подключен, пытаемся подключиться
            _LOGGER.info(f"Попытка подключения к устройству {hub._host}")
            await hub.connect()

            # Добавляем небольшую задержку после подключения для стабилизации
            await asyncio.sleep(0.2)

            _LOGGER.info(f"Успешно подключились к устройству {hub._host}")
            return True
        except Exception as e:
            _LOGGER.error(f"Не удалось подключиться к устройству {hub._host}: {e}")
            return False

    async def _scan_port(
        self, host: str, port: int, ids_port:list[int]
    ) -> List[Dict[str, Any]]:
        _LOGGER.debug("ЗАШЛИ _scan_port: %s:%s", host, port)
        """Scan a single port for devices."""
        devices = []

        _LOGGER.debug(f"_scan_port; ids_port={ids_port}")

        hub = async_modbus_hub(None, host=host, port=port)
        connecting_status = await self.async_check_and_reconnect(hub)

        # _LOGGER.debug(f"Metod update. connecting_status = {connecting_status}")
        if not connecting_status:
            _LOGGER.error(f"Не удалось подключиться к устройству {self.name}, пропускаем обновление")
            hub.disconnect()
            return devices

        for slave_id in ids_port:
            _LOGGER.debug(f"Проверяем адрес {slave_id}...")

            # Читаем регистр типа устройства
            model = await hub.async_read_holding_string(200, 20, slave_id)
            model = model.replace("-", "_").lower()

            matched_model = None

            if model is None or not model:
                continue  # Просто пропускаем, если ошибка

            _LOGGER.debug(f"Нашли устройство: type='{model}', port={port}, slave_id={slave_id}")

            if model=='wbmr6c':
                out_power = await hub.async_read_inputs(4, 1, slave_id)
                _LOGGER.debug(f"out_power='{out_power}'")
                if out_power is None:
                    matched_model = Model._member_map_.get("wbmr6c_v2")
                else:
                    matched_model = Model._member_map_.get("wbmr6c_v3")
            else:
                matched_model = Model._member_map_.get(model)

            _LOGGER.debug(f"matched_model={matched_model}")

            # Проверяем, есть ли такая модель в нашем словаре
            # Пробуем найти точное совпадение или частичное
            if matched_model:
                device_info = {
                    "host": host,
                    "port": port,
                    "slave_id": slave_id,
                    "model": matched_model,
                }

                devices.append(device_info)
                _LOGGER.debug(
                    "Найдено устройство: %s на %s:%s (адрес %s)",
                    device_info["model"],
                    host, port, slave_id
                )
            else:
                _LOGGER.warning(f"Тип устройства '{model}' не найден в списке моделей Wirenboard")

        await hub.async_disconnect()

        return devices

    async def async_step_select_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        _LOGGER.debug(f"ЗАШЛИ async_step_select_devices")
        _LOGGER.debug(f"self._discovered_devices={self._discovered_devices}")
        """Handle device selection step."""
        # Проверяем, была ли ошибка сканирования
        if self._scan_error is not None:
            _LOGGER.debug(f"async_step_select_devices шаг 1") # Если в процессе были ошибки
            return self.async_abort(
                reason="scan_failed",
                description_placeholders={
                    "error": str(self._scan_error),
                    "host": self._host,
                    "port1": self._port1,
                    "port2": self._port2,
                    "ids_port1": self._ids_port1,
                    "ids_port2": self._ids_port2,
                }
            )

        if not self._discovered_devices:
            _LOGGER.debug(f"async_step_select_devices шаг 2") # Если ничего не нашли
            return self.async_abort(
                reason="no_devices_found",
                description_placeholders={
                    "host": self._host,
                    "port1": self._port1,
                    "port2": self._port2,
                    "ids_port1": self._ids_port1,
                    "ids_port2": self._ids_port2,
                }
            )

        errors = {}

        if user_input is not None:
            # Второй вход в процедуру. Отмеченные галками устройства сохраняем в selected_devices
            _LOGGER.debug(f"async_step_select_devices шаг 3")
            selected_devices = []
            for device_key in user_input.get("selected_devices", []):
                _LOGGER.debug(f"async_step_select_devices device_key={device_key}")
                port_str, slave_str = device_key.split("_")
                port = int(port_str)
                slave_id = int(slave_str)
                _LOGGER.debug(f"async_step_select_devices port={port}, slave_id={slave_id}")

                for device in self._discovered_devices:
                    if device["port"] == port and device["slave_id"] == slave_id:
                        selected_devices.append(device)
                        break

            if not selected_devices:
                errors["base"] = "no_devices_selected"
                _LOGGER.debug(f"async_step_select_devices шаг 4")
            else:
                _LOGGER.debug(f"async_step_select_devices шаг 5")
                config_data = {
                    CONF_HOST: self._host,
                    CONF_PORT1: self._port1,
                    CONF_PORT2: self._port2,
                    CONF_DEVICES: selected_devices,
                 }

                unique_id = f"wirenboard_{self._host}_{self._port1}_{self._port2}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Wirenboard {self._host}",
                    data=config_data,
                )

        # Формируем список устройств для выбора
        _LOGGER.debug(f"async_step_select_devices шаг 6") # Первый вход в процедуру. Выбор устройств
        device_options = {}
        for device in self._discovered_devices:
            key = f"{device['port']}_{device['slave_id']}"
            display_name = (
                f"{device['model'].name} (Порт {device['port']}, "
                f"Адрес {device['slave_id']})"
            )
            device_options[key] = display_name

        _LOGGER.debug(f"async_step_select_devices шаг 7; list(device_options.keys())={list(device_options.keys())}") # Первый вход в процедуру.
        data_schema = vol.Schema({
            vol.Required(
                "selected_devices",
                default=list(device_options.keys())
            ): cv.multi_select(device_options),
        })

        return self.async_show_form(
            step_id="select_devices",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "device_count": str(len(self._discovered_devices)),
                "host": self._host,
            },
        )
#
#     @staticmethod
#     @callback
#     def async_get_options_flow(
#         config_entry: ConfigEntry,
#     ) -> OptionsFlowHandler:
#         """Create the options flow."""
#         return OptionsFlowHandler()
#
#
# class OptionsFlowHandler(OptionsFlow):
#     async def async_step_init(
#         self, user_input: dict[str, Any] | None = None
#     ) -> ConfigFlowResult:
#         """Manage the options."""
#         if user_input is not None:
#             return self.async_create_entry(data=user_input)
#
#         # Схема создается непосредственно в функции,
#         # чтобы подставить значения из конфигурации
#         option_schema = vol.Schema(
#             {
#                 vol.Required("name", default=self.config_entry.data["name"]): str,
#                 vol.Required("host_ip", default=self.config_entry.data["host_ip"]): str,
#                 vol.Required("host_port", default=self.config_entry.data["host_port"]): int,
#                 vol.Required("device_id", default=self.config_entry.data["device_id"]): int,
#                 vol.Optional("update_info"): bool,
#             }
#         )
#
#         return self.async_show_form(
#             step_id="init",
#             data_schema=self.add_suggested_values_to_schema(
#                 option_schema, self.config_entry.options
#             ),
#         )
