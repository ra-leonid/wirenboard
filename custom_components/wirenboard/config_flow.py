
from __future__ import annotations

import asyncio
from typing import Any, Optional

from pymodbus.client import  AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant import config_entries
from homeassistant.components.modbus import modbus

from .const import DOMAIN
from .registers import WBSmartRegisters

STEP_TCP_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("name", default="WB_Smart"): str,
        vol.Required("host_ip", default="192.168.0.7"): str,
        vol.Required("host_port", default=502): int,
        vol.Required("device_type", default="wb-mr6c"): str,
        vol.Required("device_id", default=116): int,
    }
)

async def async_validate_device(port, address: str | None, device_type:int, device_id:int) -> None:
    # Простая валидация - считаем что устройство доступно
    # Детальная проверка будет происходить при инициализации интеграции
    # TODO Реализовать проверку заполнения свойств
    pass


class WBSmartConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    data: Optional[dict(str, Any)]

    async def async_step_user(self, user_input: Optional[dict(str, Any)] = None):
        """Invoke when a user initiates a flow via the user interface."""
        return await self.async_step_tcp(user_input)



    async def async_step_tcp(self, user_input: Optional[dict(str, Any)] = None):
        """Configure ModBus TCP entry."""
        errors: dict(str, str) = {}

        if user_input is not None:
            try:
                await async_validate_device(
                    user_input["host_port"],
                    user_input["host_ip"],
                    user_input["device_type"],
                    user_input["device_id"],
                )
            except ValueError as error:
                errors["base"] = str(error)
            if not errors:
                # Input is valid, set data.
                self.data = user_input

                await asyncio.sleep(1)
                return self.async_create_entry(title=user_input["name"], data=self.data)
        return self.async_show_form(
            step_id="tcp", data_schema=STEP_TCP_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlowHandler:
        """Create the options flow."""
        return OptionsFlowHandler()

class OptionsFlowHandler(OptionsFlow):
    # Здесь точка входа async_step_init,
    # в остальном все аналогично ConfigFlow
    async def async_step_init(self, user_input: dict = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input.pop("update_info", False):
                #session = async_get_clientsession(self.hass)
                #radio = Karadio32Api(self.config_entry.data[CONF_URL], session)
                try:
                    user_input["host_port"] = self.config_entry.data["host_port"]
                    user_input["host_ip"] = self.config_entry.data["host_ip"]
                    user_input["device_type"] = self.config_entry.data["device_type"]
                    user_input["device_id"] = self.config_entry.data["device_id"]
                except Exception as e:
                    errors["base"] = str(e)

            if not errors:
                # Если все ОК, то обновляем запись об интеграции
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=user_input
                )
                # Подаем сигнал, что все ОК, но не создаем новых объектов
                return self.async_create_entry(title=None, data=None)

        # Схема создается непосредственно в функции,
        # чтобы подставить значения из конфигурации
        option_schema = vol.Schema(
            {
                vol.Required("name", default=self.config_entry.data["name"]): str,
                vol.Required("host_ip", default=self.config_entry.data["host_ip"]): str,
                vol.Required("host_port", default=self.config_entry.data["host_port"]): int,
                vol.Required("device_type", default=self.config_entry.data["device_type"]): str,
                vol.Required("device_id", default=self.config_entry.data["device_id"]): int,
                vol.Optional("update_info"): bool,
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=option_schema, errors=errors
        )
