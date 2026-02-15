"""Config flow for Wirenboard Modbus integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

import voluptuous as vol
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
)
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    DEFAULT_PORT1,
    DEFAULT_PORT2,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    CONF_SLAVE_ID,
    CONF_TIMEOUT,
    CONF_PORT1,
    CONF_PORT2,
    CONF_DEVICES,
    MIN_SLAVE_ID,
    MAX_SLAVE_ID,
    WIRENBOARD_MODELS,
)

_LOGGER = logging.getLogger(__name__)

# Глобальный словарь для хранения задач сканирования
_SCANNING_TASKS: Dict[str, asyncio.Task] = {}


class WirenboardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Wirenboard with WB-MGE v.3."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._host: str | None = None
        self._port1: int | None = None
        self._port2: int | None = None
        self._discovered_devices: List[Dict[str, Any]] = []
        self._scan_error: Exception | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        _LOGGER.info(f"ЗАШЛИ async_step_user. CONF_HOST={CONF_HOST}")
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port1 = user_input[CONF_PORT1]
            self._port2 = user_input[CONF_PORT2]

            # Переходим к сканированию
            return await self.async_step_scan()

        data_schema = vol.Schema({
            vol.Required(CONF_HOST, default="192.168.0.7"): cv.string,
            vol.Required(CONF_PORT1, default=DEFAULT_PORT1): cv.port,
            vol.Required(CONF_PORT2, default=DEFAULT_PORT2): cv.port,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        _LOGGER.info("ЗАШЛИ async_step_scan")
        """Handle the scanning step."""
        if user_input is None:
            return self.async_show_form(
                step_id="scan",
                description_placeholders={
                    "host": self._host,
                    "port1": self._port1,
                    "port2": self._port2,
                },
                data_schema=vol.Schema({}),
            )

        # Создаем и запускаем задачу сканирования
        scanning_task = self.hass.async_create_task(
            self._scan_devices()
        )

        # Сохраняем задачу в глобальном словаре
        _SCANNING_TASKS[self.flow_id] = scanning_task

        # Показываем прогресс
        return self.async_show_progress(
            step_id="scan_progress",
            progress_action="scanning",
            progress_task=scanning_task,
            description_placeholders={
                "host": self._host,
                "port1": self._port1,
                "port2": self._port2,
            },
        )

    async def async_step_scan_progress(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        _LOGGER.info("ЗАШЛИ async_step_scan_progress")
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
                self._scan_error = None
            except Exception as ex:
                # Ошибка
                self._scan_error = ex
                _LOGGER.error("Scanning failed: %s", ex, exc_info=True)
            finally:
                # Удаляем задачу из глобального словаря
                _SCANNING_TASKS.pop(self.flow_id, None)

            # Всегда переходим к выбору устройств после завершения прогресса
            return self.async_show_progress_done(next_step_id="select_devices")

        # Если задача еще не завершена, продолжаем ждать
        return self.async_show_progress_done(next_step_id="scan_progress")

    async def _scan_devices(self) -> None:
        """Scan for devices on both ports."""
        _LOGGER.info("ЗАШЛИ _scan_devices")
        self._discovered_devices = []

        try:
            # Сканируем порты
            _LOGGER.info(f"Начинаем сканирование порта {self._port1}")
            devices_port1 = await self._scan_port(self._host, self._port1)
            self._discovered_devices.extend(devices_port1)

            _LOGGER.info(f"Начинаем сканирование порта {self._port2}")
            devices_port2 = await self._scan_port(self._host, self._port2)
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

    async def _scan_port(
        self, host: str, port: int
    ) -> List[Dict[str, Any]]:
        _LOGGER.info("ЗАШЛИ _scan_port: %s:%s", host, port)
        """Scan a single port for devices."""
        devices = []
        client = None

        try:
            client = AsyncModbusTcpClient(
                host=host,
                port=port,
                retries=1,
                timeout=3.0,
            )

            await client.connect()

            if not client.connected:
                _LOGGER.error("Не удалось подключиться к %s:%s", host, port)
                return devices

            # Сканируем все возможные slave ID
            _LOGGER.info(f"Сканируем адреса с {MIN_SLAVE_ID} по {MAX_SLAVE_ID}")

            for slave_id in range(MIN_SLAVE_ID, MAX_SLAVE_ID + 1):
                # Пропускаем проверку для скорости, но оставляем логирование
                if slave_id % 10 == 0:
                    _LOGGER.info(f"Проверяем адрес {slave_id}...")

                try:
                    # Читаем регистр типа устройства
                    response = await client.read_holding_registers(
                        address=0x00C8,  # Регистр типа устройства Wirenboard
                        count=20,
                        device_id=slave_id  # Используем device_id вместо slave
                    )

                    if response.isError():
                        continue  # Просто пропускаем, если ошибка

                    # Проверяем наличие регистров
                    if not hasattr(response, 'registers') or not response.registers:
                        continue

                    # Убираем нули в конце
                    registers = response.registers.copy()
                    while registers and registers[-1] == 0:
                        registers.pop()

                    if not registers:  # Если все регистры нулевые
                        continue

                    # Преобразуем регистры в строку (каждый регистр = 2 символа)
                    device_type_str = ""
                    for reg in registers:
                        # Каждый регистр содержит 2 байта
                        char1 = reg & 0xFF  # Младший байт
                        char2 = (reg >> 8) & 0xFF  # Старший байт

                        # Добавляем символы, если они не нулевые
                        if char1:
                            device_type_str += chr(char1)
                        if char2:
                            device_type_str += chr(char2)

                    # Убираем нулевые символы и пробелы
                    device_type_str = device_type_str.strip('\x00 \t\n\r')

                    if not device_type_str:
                        continue  # Если строка пустая, пропускаем

                    _LOGGER.info(f"Нашли устройство: type='{device_type_str}', port={port}, slave_id={slave_id}")

                    # Проверяем, есть ли такая модель в нашем словаре
                    # Пробуем найти точное совпадение или частичное
                    matched_model = None
                    for model_key in WIRENBOARD_MODELS:
                        if model_key in device_type_str or device_type_str in model_key:
                            matched_model = model_key
                            break

                    if matched_model:
                        device_info = {
                            "host": host,
                            "port": port,
                            "slave_id": slave_id,
                            "device_type": device_type_str,
                            "model": WIRENBOARD_MODELS[matched_model],
                            "firmware_version": registers[1] if len(registers) > 1 else 0,
                        }

                        # Пробуем получить серийный номер
                        try:
                            serial_response = await client.read_holding_registers(
                                address=0x0002,
                                count=4,
                                device_id=slave_id  # Используем device_id
                            )
                            if not serial_response.isError() and hasattr(serial_response, 'registers'):
                                serial_parts = []
                                for reg in serial_response.registers:
                                    serial_parts.append(f"{reg:04x}")
                                device_info["serial_number"] = "-".join(serial_parts)
                        except Exception as e:
                            _LOGGER.debug("Не удалось прочитать серийный номер: %s", e)

                        devices.append(device_info)
                        _LOGGER.info(
                            "Найдено устройство: %s на %s:%s (адрес %s)",
                            device_info["model"],
                            host, port, slave_id
                        )
                    else:
                        _LOGGER.info(f"Тип устройства '{device_type_str}' не найден в списке моделей Wirenboard")

                except (ModbusException, asyncio.TimeoutError) as e:
                    # Это нормально для устройств, которых нет
                    continue
                except Exception as e:
                    _LOGGER.debug(
                        "Ошибка сканирования адреса %s на %s:%s: %s",
                        slave_id, host, port, e
                    )
                    continue

        except Exception as e:
            _LOGGER.error("Ошибка в _scan_port: %s", e, exc_info=True)
            raise
        finally:
            # Безопасное закрытие клиента
            if client is not None:
                try:
                    # Пробуем разные методы закрытия
                    if hasattr(client, 'async_close'):
                        await client.async_close()
                    elif hasattr(client, 'close'):
                        if asyncio.iscoroutinefunction(client.close):
                            await client.close()
                        else:
                            client.close()
                except Exception as e:
                    _LOGGER.debug("Ошибка при закрытии клиента: %s", e)

        _LOGGER.info(f"Сканирование порта {port} завершено. Найдено устройств: {len(devices)}")
        return devices

    async def async_step_select_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        _LOGGER.info("ЗАШЛИ async_step_select_devices")
        """Handle device selection step."""
        # Проверяем, была ли ошибка сканирования
        if self._scan_error is not None:
            return self.async_abort(
                reason="scan_failed",
                description_placeholders={
                    "error": str(self._scan_error),
                    "host": self._host,
                    "port1": self._port1,
                    "port2": self._port2,
                }
            )

        if not self._discovered_devices:
            return self.async_abort(
                reason="no_devices_found",
                description_placeholders={
                    "host": self._host,
                    "port1": self._port1,
                    "port2": self._port2,
                }
            )

        errors = {}

        if user_input is not None:
            selected_devices = []
            for device_key in user_input.get("selected_devices", []):
                port_str, slave_str = device_key.split("_")
                port = int(port_str)
                slave_id = int(slave_str)

                for device in self._discovered_devices:
                    if device["port"] == port and device["slave_id"] == slave_id:
                        selected_devices.append(device)
                        break

            if not selected_devices:
                errors["base"] = "no_devices_selected"
            else:
                config_data = {
                    CONF_HOST: self._host,
                    CONF_PORT1: self._port1,
                    CONF_PORT2: self._port2,
                    CONF_DEVICES: selected_devices,
                    CONF_SCAN_INTERVAL: user_input.get(
                        CONF_SCAN_INTERVAL,
                        DEFAULT_SCAN_INTERVAL
                    ),
                    CONF_TIMEOUT: user_input.get(
                        CONF_TIMEOUT,
                        DEFAULT_TIMEOUT
                    ),
                }

                unique_id = f"wirenboard_{self._host}_{self._port1}_{self._port2}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Wirenboard {self._host}",
                    data=config_data,
                )

        # Формируем список устройств для выбора
        device_options = {}
        for device in self._discovered_devices:
            key = f"{device['port']}_{device['slave_id']}"
            display_name = (
                f"{device['model']} (Порт {device['port']}, "
                f"Адрес {device['slave_id']})"
            )
            device_options[key] = display_name

        data_schema = vol.Schema({
            vol.Required(
                "selected_devices",
                default=list(device_options.keys())
            ): cv.multi_select(device_options),
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=DEFAULT_SCAN_INTERVAL
            ): vol.All(
                vol.Coerce(int),
                vol.Range(min=5, max=3600)
            ),
            vol.Optional(
                CONF_TIMEOUT,
                default=DEFAULT_TIMEOUT
            ): vol.All(
                vol.Coerce(float),
                vol.Range(min=1.0, max=30.0)
            ),
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

    async def async_step_import(self, import_config: dict[str, Any]) -> FlowResult:
        _LOGGER.info("ЗАШЛИ async_step_import")
        """Handle import from configuration.yaml."""
        _LOGGER.warning(
            "Configuration via YAML is deprecated. "
            "Please use the UI to configure Wirenboard integration."
        )

        host = import_config[CONF_HOST]
        port1 = import_config.get(CONF_PORT1, DEFAULT_PORT1)
        port2 = import_config.get(CONF_PORT2, DEFAULT_PORT2)

        config_data = {
            CONF_HOST: host,
            CONF_PORT1: port1,
            CONF_PORT2: port2,
            CONF_SCAN_INTERVAL: import_config.get(
                CONF_SCAN_INTERVAL,
                DEFAULT_SCAN_INTERVAL
            ),
            CONF_TIMEOUT: import_config.get(
                CONF_TIMEOUT,
                DEFAULT_TIMEOUT
            ),
        }

        if "devices" in import_config:
            config_data[CONF_DEVICES] = import_config["devices"]

        unique_id = f"wirenboard_{host}_{port1}_{port2}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"Wirenboard {host} (Imported)",
            data=config_data,
        )