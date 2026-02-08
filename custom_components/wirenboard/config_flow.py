
from __future__ import annotations

import asyncio
from typing import Any, Optional

# from pymodbus.client import  AsyncModbusTcpClient
# from pymodbus.exceptions import ModbusException
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow, ConfigFlowResult
from homeassistant.core import callback
from homeassistant import config_entries
# from homeassistant.components.modbus import modbus

from .const import DOMAIN

STEP_TCP_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("name", default="WB_Smart"): str,
        vol.Required("host_ip", default="192.168.0.7"): str,
        vol.Required("host_port", default=502): int,
        vol.Required("device_id", default=116): int,
    }
)

async def async_validate_device(port, address: str | None, device_id:int) -> None:
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
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        # Схема создается непосредственно в функции,
        # чтобы подставить значения из конфигурации
        option_schema = vol.Schema(
            {
                vol.Required("name", default=self.config_entry.data["name"]): str,
                vol.Required("host_ip", default=self.config_entry.data["host_ip"]): str,
                vol.Required("host_port", default=self.config_entry.data["host_port"]): int,
                vol.Required("device_id", default=self.config_entry.data["device_id"]): int,
                vol.Optional("update_info"): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                option_schema, self.config_entry.options
            ),
        )
