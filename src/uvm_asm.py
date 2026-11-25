import argparse
import csv
from pathlib import Path

from src.uvm_isa import COMMANDS, b_limit, encode, hex_bytes


def error(message):
    raise SystemExit(f"Ошибка: {message}")


def parse_args():
    parser = argparse.ArgumentParser(description="Ассемблер учебной ВМ")
    parser.add_argument("source", help="текст программы на ассемблере (CSV)")
    parser.add_argument("output", help="двоичный файл-результат")
    parser.add_argument(
        "-t", "--test", action="store_true", help="режим тестирования"
    )
    return parser.parse_args()


def read_source(path):
    try:
        return Path(path).read_text(encoding="utf-8-sig")
    except OSError as exc:
        error(f"не удалось открыть {path}: {exc}")
    except UnicodeDecodeError:
        error(f"{path} не в кодировке UTF-8")


def parse_operand(text, line_no):
    try:
        return int(text, 0)
    except ValueError:
        error(f"строка {line_no}: операнд «{text}» не является целым числом")


def parse_row(row, line_no):
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
    program = []
    for line_no, row in enumerate(csv.reader(text.splitlines()), 1):
        if not row or not "".join(row).strip():
            continue
        if row[0].lstrip().startswith("#"):
            continue
        program.append(parse_row(row, line_no))
    return program


def translate(program):
    return b"".join(encode(command) for command in program)


def write_binary(path, code):
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(code)
    except OSError as exc:
        error(f"не удалось записать {path}: {exc}")


def print_bytes(program):
    for command in program:
        line = f"{command['name']},{command['B']}"
        print(f"{line:<11} -> {hex_bytes(encode(command))}")


def main():
    args = parse_args()
    program = parse(read_source(args.source))
    if not program:
        error("в программе нет ни одной команды")
    code = translate(program)
    write_binary(args.output, code)
    if args.test:
        print_bytes(program)
    print(f"Команд: {len(program)}. Размер файла {args.output}: "
          f"{len(code)} байт")
