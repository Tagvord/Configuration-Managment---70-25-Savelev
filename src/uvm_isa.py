COMMAND_SIZE = 3
OPCODE_BITS = 7

COMMANDS = {
    "load": (119, 15, "константа"),
    "read": (16, 14, "смещение"),
    "write": (89, 12, "адрес"),
    "eq": (38, 12, "адрес"),
}


def b_limit(name):
    return (1 << COMMANDS[name][1]) - 1


def encode(command):
    word = command["A"] | command["B"] << OPCODE_BITS
    return word.to_bytes(COMMAND_SIZE, "little")


def hex_bytes(data):
    return ", ".join(f"0x{byte:02X}" for byte in data)


OPCODES = {opcode: name for name, (opcode, _, _) in COMMANDS.items()}


def decode(data):
    word = int.from_bytes(data, "little")
    opcode = word & ((1 << OPCODE_BITS) - 1)
    if opcode not in OPCODES:
        raise ValueError(f"неизвестный код операции {opcode}")
    name = OPCODES[opcode]
    operand = (word >> OPCODE_BITS) & b_limit(name)
    return {"name": name, "A": opcode, "B": operand}
