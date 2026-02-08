from __future__ import annotations

import logging
import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .device import WBMr
from .coordinator import WBCoordinator

PLATFORMS = [
    #"binary_sensor",
    "select",
    "sensor",
    "switch",
    "number",
]

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:

    name = entry.data["name"]
    host_ip = entry.data["host_ip"]
    host_port = entry.data["host_port"]
    device_id = entry.data["device_id"]

    hass.data.setdefault(DOMAIN, {})
    wb_device = WBMr(hass, host_ip, host_port, device_id)

    wb_coordinator = WBCoordinator(hass, entry, wb_device)

    hass.data[DOMAIN][entry.entry_id] = wb_coordinator

    _LOGGER.info(f"Создано устройство {wb_device.name}")

    # Извлекает исходные данные, чтобы они у нас были при подписке на объекты
    # Если обновление завершится неудачно, async_config_entry_first_refresh поднимет ConfigEntryNotReady
    # и программа установки повторит попытку позже
    try:
        async with async_timeout.timeout(20):
            await wb_coordinator.async_config_entry_first_refresh()
    except ValueError as ex:
        raise ConfigEntryNotReady(f"Timeout while connecting {host_ip}") from ex
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # TODO Реализовать отключение соединения по MODBUS
        #hass.data[DOMAIN][entry.entry_id]._hub.disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
