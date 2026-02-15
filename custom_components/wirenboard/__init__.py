from __future__ import annotations

import logging
import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_NAME,
    # CONF_SCAN_INTERVAL,
)

from .device import Model, Platform, WBMR6C, WBMCM8
from .coordinator import WBCoordinator

from .const import (
    DOMAIN,
    CONF_DEVICES,
    CONF_PORT1,
    CONF_PORT2
)

# PLATFORMS = Platform._member_names_

PLATFORMS = [
    # "binary_sensor",
    "select",
    "sensor",
    "switch",
    "number",
]

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:

    hass.data.setdefault(DOMAIN, {})

    selected_devices = entry.data.get(CONF_DEVICES, [])
    _LOGGER.debug(f"selected_devices={selected_devices}")

    wb_coordinator = WBCoordinator(hass, entry)

    for device in selected_devices:
        _LOGGER.info(f"device={device}")
        wb_device = None

        match device["model"]:
            case Model.wbmr6c_v2:
                wb_device = WBMR6C(hass, wb_coordinator, device["host"], device["port"], device["slave_id"], device["model"])
            # case Model.wbmcm8:
            #     wb_device = WBMCM8(hass, wb_coordinator, device["host"], device["port"], device["slave_id"], device["model"])
            case _:
                continue

        if not wb_device is None:
            _LOGGER.info(f"Создано устройство {wb_device.name}")
            wb_coordinator.add_device(wb_device)

    hass.data[DOMAIN][entry.entry_id] = wb_coordinator

    # Извлекает исходные данные, чтобы они у нас были при подписке на объекты
    # Если обновление завершится неудачно, async_config_entry_first_refresh поднимет ConfigEntryNotReady
    # и программа установки повторит попытку позже
    try:
        async with async_timeout.timeout(20):
            _LOGGER.debug(f"await wb_coordinator.async_config_entry_first_refresh()")
            await wb_coordinator.async_config_entry_first_refresh()
    except ValueError as ex:
        raise ConfigEntryNotReady(f"Timeout while connecting {entry.data.get(CONF_HOST, "")}") from ex

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )

    _LOGGER.debug(f"Выход async_setup_entry")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # TODO Реализовать отключение соединения по MODBUS
        #hass.data[DOMAIN][entry.entry_id]._hub.disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
