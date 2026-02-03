class WBMRRegisters:
    relay_statuses_addr = 0
    relay_count = 6
    input_mode_addr = 9
    input_mode_0_addr = 16
    status_outputs_when_power_applied_addr = 6
    time_suppression_addr = 20
    time_suppression_0_addr = 27
    INPUT_MODE_VALUES = {
        0: "Кнопка без фиксации",
        1: "Переключатель с фиксацией",
        2: "Отключить все выходы",
        3: "Управление отключено, вход измеряет частоту",
        4: "Управлять по mapping-матрице",
        6: "Управлять по mapping-матрице для кнопок",
    }
    INPUT_MODE_VALUES_0 = {
        2: "Отключить все выходы",
        3: "Управление отключено, вход измеряет частоту",
        4: "Управлять по mapping-матрице",
        6: "Управлять по mapping-матрице для кнопок",
    }
    STATUS_OUTPUTS_WHEN_POWER_APPLIED = {
        0: "Перевести в безопасное состояние",
        1: "Восстановить последнее состояние",
        2: "Установить состояние выхода согласно состоянию входа",
    }