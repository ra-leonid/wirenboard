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
DEFAULT_SLAVE_IDS_PORT1 = "116, 73"
DEFAULT_SLAVE_IDS_PORT2 = "247"

# Error messages
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_NO_DEVICES_FOUND = "no_devices_found"
ERROR_NO_DEVICES_SELECTED = "no_devices_selected"
ERROR_SCAN_FAILED = "scan_failed"

PORT_SPEED = {
    12: "1200 бит/с",
    24: "2400 бит/с",
    48: "4800 бит/с",
    96: "9600 бит/с",
    192: "19 200 бит/с",
    384: "38 400 бит/с",
    576: "57 600 бит/с",
    1152: "115 200 бит/с",
}

PARITY_MODE = {
    0: "нет бита чётности",
    1: "нечётный",
    2: "чётный",
}

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

MDM_DIM_CURVE = {
    0: "Логарифмическая для с/д или лампы накаливания",
    1: "Линейная для резистивной нагрузки",
    2: "Ключевой режим",
}

MDM_DIM_MODE = {
    0: "По переднему фронту",
    1: "По заднему фронту",
}

MDM_INPUT_MODE = {
    0: "Кнопка",
    1: "Выключатель с фиксацией",
}

MDM_PRESS_ACTION_INPUT = {
    0: "Событие игнорируется",
    1: "Действие на 1 выходе",
    2: "Действие на 2 выходе",
    3: "Действие на 3 выходе",
    100: "Действие на всех выходах"
}

MDM_PRESS_ACTION = {
    0: "Отключить выход",
    1: "Включить выход",
    2: "Переключить состояние выхода",
    3: "Уменьшить уровень",
    4: "Увеличить уровень",
    5: "Увеличить/уменьшить уровень"
}
