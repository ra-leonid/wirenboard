"""Constants for Wirenboard Modbus integration."""

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

# Default values
DEFAULT_PORT1 = 502
DEFAULT_PORT2 = 503
DEFAULT_SCAN_INTERVAL = 600  # seconds
DEFAULT_TIMEOUT = 600.0  # seconds

# Scanning parameters
MIN_SLAVE_ID = 114
MAX_SLAVE_ID = 130  # Стандартный диапазон Modbus

# Wirenboard device models
WIRENBOARD_MODELS = {
    "WBMR6C": "WB-MR6C v.2",
    "WBMIO": "WB-MGE v.3",
}

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