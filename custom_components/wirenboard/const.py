DOMAIN = "wirenboard"

# Configuration
CONF_SLAVE_ID = "slave_id"
CONF_TIMEOUT = "timeout"
CONF_PORT1 = "port1"
CONF_PORT2 = "port2"
CONF_DEVICES = "devices"
CONF_MODEL = "model"
CONF_DEVICE_TYPE = "device_type"
CONF_SERIAL_NUMBER = "serial_number"
CONF_SLAVE_IDS_PORT1 = "ids_slave_port1"
CONF_SLAVE_IDS_PORT2 = "ids_slave_port2"

# Default values
DEFAULT_IP = "192.168.0.7"
DEFAULT_PORT1 = 502
DEFAULT_PORT2 = 503
DEFAULT_SLAVE_IDS_PORT1 = "116, 73, 50, 69"
DEFAULT_SLAVE_IDS_PORT2 = "247"

# Modbus registers
REGISTER_DEVICE_TYPE = 0x00C8
REGISTER_FIRMWARE_VERSION = 0x00FA
REGISTER_SERIAL_NUMBER_START = 0x0270  # 4 регистра
REGISTER_HARDWARE_VERSION = 0x0290

# Error messages
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_NO_DEVICES_FOUND = "no_devices_found"
ERROR_NO_DEVICES_SELECTED = "no_devices_selected"
ERROR_SCAN_FAILED = "scan_failed"

MR_INPUT_MODE = {
    0: "Кнопка без фиксации",
    1: "Переключатель с фиксацией",
    2: "Отключить все выходы",
    3: "Управление отключено, вход измеряет частоту",
    4: "Управлять по mapping-матрице",
    6: "Управлять по mapping-матрице для кнопок",
}
MR_INPUT_MODE_0 = {
    2: "Отключить все выходы",
    3: "Управление отключено, вход измеряет частоту",
    4: "Управлять по mapping-матрице",
    6: "Управлять по mapping-матрице для кнопок",
}
MR_STATUS_OUTPUTS_WHEN_POWER_APPLIED = {
    0: "Перевести в безопасное состояние",
    1: "Восстановить последнее состояние",
    2: "Установить состояние выхода согласно состоянию входа",
}
MSM_INPUT_MODE = {
    0: "Измерять частоту вх. сигнала",
    1: "Использовать вх. как кн. для детектирования нажатий",
}
