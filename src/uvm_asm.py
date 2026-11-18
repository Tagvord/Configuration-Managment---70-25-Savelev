
import argparse
import csv
from pathlib import Path

from src.uvm_isa import COMMANDS, b_limit


def error(message):
    """Завершает программу с сообщением об ошибке."""
    raise SystemExit(f"Ошибка: {message}")


def parse_args():
    """Разбирает аргументы командной строки."""
    parser = argparse.ArgumentParser(description="Ассемблер учебной ВМ")
    parser.add_argument("source", help="текст программы на ассемблере (CSV)")
    parser.add_argument("output", help="двоичный файл-результат")
    parser.add_argument(
        "-t", "--test", action="store_true", help="режим тестирования"
    )
    return parser.parse_args()


def read_source(path):
    """Читает текст программы"""
    try:
        return Path(path).read_text(encoding="utf-8-sig")
    except OSError as exc:
        error(f"не удалось открыть {path}: {exc}")
    except UnicodeDecodeError:
        error(f"{path} не в кодировке UTF-8")


def parse_operand(text, line_no):
    """Переводит операнд в число: 668, 0x29C и 0b1010 тоже подходят."""
    try:
        return int(text, 0)
    except ValueError:
        error(f"строка {line_no}: операнд «{text}» не является целым числом")


def parse_row(row, line_no):
    """Превращает строку CSV в команду промежуточного представления."""
    name = row[0].strip().lower()
    if name not in COMMANDS:
        error(f"строка {line_no}: неизвестная команда «{row[0].strip()}»")
    if len(row) != 2 or not row[1].strip():
        error(f"строка {line_no}: команда {name} ожидает ровно один операнд")
    value = parse_operand(row[1].strip(), line_no)
    if not 0 <= value <= b_limit(name):
        error(
            f"строка {line_no}: операнд {value} команды {name} "
            f"вне диапазона 0..{b_limit(name)}"
        )
    return {"name": name, "A": COMMANDS[name][0], "B": value, "line": line_no}


def parse(text):
    """Переводит текст программы в список команд."""
    program = []
    for line_no, row in enumerate(csv.reader(text.splitlines()), 1):
        if not row or not "".join(row).strip():
            continue
        if row[0].lstrip().startswith("#"):
            continue
        program.append(parse_row(row, line_no))
    return program


def print_ir(program):
    """Печатает промежуточное представление в виде полей и значений."""
    for index, command in enumerate(program):
        print(
            f"{index:3}: {command['name']:<5} "
            f"A={command['A']}, B={command['B']}"
        )


def main():
    args = parse_args()
    program = parse(read_source(args.source))
    if not program:
        error("в программе нет ни одной команды")
    if args.test:
        print_ir(program)
    print(f"Команд в программе: {len(program)}")
