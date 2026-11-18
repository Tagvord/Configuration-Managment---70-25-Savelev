
COMMAND_SIZE = 3
OPCODE_BITS = 7


COMMANDS = {
    "load": (119, 15, "константа"),
    "read": (16, 14, "смещение"),
    "write": (89, 12, "адрес"),
    "eq": (38, 12, "адрес"),
}


def b_limit(name):
    """Возвращает наибольшее значение поля B для команды."""
    return (1 << COMMANDS[name][1]) - 1
