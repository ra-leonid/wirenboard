from __future__ import annotations

# import logging
import asyncio
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .device import WBMr
PLATFORMS = [
    #"binary_sensor",
    "select",
    #"sensor",
    "switch",
]

# _LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    name = entry.data["name"]
    host_ip = entry.data["host_ip"]
    host_port = entry.data["host_port"]
    device_id = entry.data["device_id"]
    device_type = entry.data["device_type"]
    device = WBMr(hass, host_ip, host_port, device_type, device_id)
    try:
        await device.update()
        await device.update_setting()
    except ValueError as ex:
        raise ConfigEntryNotReady(f"Timeout while connecting {host_ip}") from ex
    hass.data[DOMAIN][entry.entry_id] = device
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

