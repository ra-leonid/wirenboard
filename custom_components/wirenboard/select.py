import logging

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .device import WBMr
from datetime import timedelta


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(HomeAssistant, config_entry, async_add_entities):

    device: WBMr = HomeAssistant.data[DOMAIN][config_entry.entry_id]

    selects = []

    # Состояние выходов при подаче питания
    selects.append(status_outputs_when_power_applied(device))

    # Режимы работы входов
    for i in range(device.input_count):
        selects.append(wb_input_mode(device, i))
        _LOGGER.info(f"📊 СОЗДАН {i} выбор")

    _LOGGER.info(f"📊 СОЗДАНО {len(selects)} полей выбора")
    async_add_entities(selects, update_before_add=False)

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


SCAN_INTERVAL = timedelta(seconds=15)
class wb_input_mode(SelectEntity):
    _attr_current_option: str | None = None
    _attr_entity_registry_enabled_default = True
    _attr_icon = "mdi:button-pointer"

    def __init__(self, device: WBMr, channel: int):
        self._attr_name = f"Режим работы входа {channel}"
        # self._attr_unique_id = self._attr_name
        self._attr_unique_id = f"{device.name}_select_{channel}"
        self.entity_id = f"{device.name}.select.{channel}"
        self._attr_available = True
        self._attr_entity_category = EntityCategory.CONFIG  # DIAGNOSTIC

        self._device = device
        self._channel = channel

        self._attr_options = self._device.get_attr_options("input_mode", self._channel)
        self.current_option = self.get_current_option()

    async def async_update(self):
        self.current_option = self.get_current_option()
        self._attr_available = self._device.is_connected

    async def async_select_option(self, option: str) -> None:
        await self._device.set_input_mode(self._channel, option)

    def get_current_option(self):
        return self._device.get_switch_input_mode(self._channel)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.name)}
        }


class status_outputs_when_power_applied(SelectEntity):
    _attr_current_option: str | None = None
    _attr_entity_registry_enabled_default = True
    _attr_icon = "mdi:list-status"

    def __init__(self, device: WBMr):
        self._attr_name = f"Состояния выходов при подаче питания"
        # self._attr_unique_id = self._attr_name
        self._attr_unique_id = f"{device.name}_select_status_outputs_when_power_applied"
        self.entity_id = f"{device.name}.select.status_outputs_when_power_applied"
        self._attr_available = True
        self._attr_entity_category = EntityCategory.CONFIG  # DIAGNOSTIC

        self._device = device

        self._attr_options = self._device.get_attr_options("status_outputs_when_power_applied")
        self.current_option = self.get_current_option()

    async def async_update(self):
        self.current_option = self.get_current_option()
        self._attr_available = self._device.is_connected

    async def async_select_option(self, option: str) -> None:
        await self._device.set_status_outputs_when_power_applied(option)

    def get_current_option(self):
        return self._device.get_status_outputs_when_power_applied()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.name)}
        }
