import argparse
import json
from pathlib import Path

from src.uvm_isa import COMMAND_SIZE, decode

MEMORY_SIZE = 1 << 16


def error(message):
    raise SystemExit(f"Ошибка: {message}")


def parse_args():
    parser = argparse.ArgumentParser(description="Интерпретатор учебной ВМ")
    parser.add_argument("program", help="двоичный файл с программой")
    parser.add_argument("dump", help="файл для дампа памяти (JSON)")
    parser.add_argument("range", help="диапазон адресов дампа, напр. 100:119")
    return parser.parse_args()


def parse_range(text):
    try:
        start, end = (int(part, 0) for part in text.split(":"))
    except ValueError:
        error(f"диапазон «{text}» должен иметь вид начало:конец")
    if not 0 <= start <= end < MEMORY_SIZE:
        error(f"диапазон {start}:{end} вне памяти 0..{MEMORY_SIZE - 1}")
    return start, end


class Machine:

    def __init__(self, code):
        if len(code) % COMMAND_SIZE:
            error(f"размер программы ({len(code)} байт) не кратен 3")
        if len(code) > MEMORY_SIZE:
            error("программа не помещается в память")
        self.memory = [0] * MEMORY_SIZE
        self.memory[:len(code)] = code
        self.code_end = len(code)
        self.pc = 0
        self.stack = []
        self.steps = 0
        self.handlers = {
            "load": self.load,
            "read": self.read,
            "write": self.write,
            "eq": self.eq,
        }

    def run(self):
        while self.pc < self.code_end:
            command = self.fetch()
            self.pc += COMMAND_SIZE
            self.execute(command)
            self.steps += 1

    def fetch(self):
        cells = self.memory[self.pc:self.pc + COMMAND_SIZE]
        if any(not 0 <= cell <= 255 for cell in cells):
            error(f"адрес {self.pc}: в памяти команд не байт")
        try:
            return decode(bytes(cells))
        except ValueError as exc:
            error(f"адрес {self.pc}: {exc}")

    def execute(self, command):
        handler = self.handlers.get(command["name"])
        if handler is None:
            error(f"команда {command['name']} не реализована")
        handler(command["B"])

    def push(self, value):
        self.stack.append(value)

    def pop(self):
        if not self.stack:
            error(f"адрес {self.pc - COMMAND_SIZE}: стек пуст")
        return self.stack.pop()

    def check_address(self, address):
        if not 0 <= address < MEMORY_SIZE:
            error(f"адрес {address} вне памяти 0..{MEMORY_SIZE - 1}")
        return address

    def load(self, constant):
        self.push(constant)

    def read(self, offset):
        address = self.check_address(self.pop() + offset)
        self.push(self.memory[address])

    def write(self, address):
        self.memory[self.check_address(address)] = self.pop()

    def eq(self, address):
        first = self.pop()
        second = self.memory[self.check_address(address)]
        self.push(int(first == second))


def read_program(path):
    try:
        return Path(path).read_bytes()
    except OSError as exc:
        error(f"не удалось открыть {path}: {exc}")


def save_dump(memory, start, end, path):
    dump = {str(address): memory[address] for address in range(start, end + 1)}
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dump, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        error(f"не удалось записать {path}: {exc}")


def print_dump(memory, start, end, per_line=10):
    for row in range(start, end + 1, per_line):
        values = memory[row:min(row + per_line, end + 1)]
        print(f"{row:5}: " + " ".join(f"{value:5}" for value in values))


def main():
    args = parse_args()
    start, end = parse_range(args.range)
    machine = Machine(read_program(args.program))
    machine.run()
    save_dump(machine.memory, start, end, args.dump)
    print(f"Выполнено команд: {machine.steps}, стек: {machine.stack}")
    print(f"Дамп ячеек {start}..{end} сохранён в {args.dump}")
    print_dump(machine.memory, start, end)
