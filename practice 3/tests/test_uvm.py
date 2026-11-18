"""Проверки УВМ.

Запуск из папки practice 3: python -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

PRACTICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRACTICE.parent))

from src.uvm_asm import parse  # noqa: E402

EXAMPLES = PRACTICE / "examples"


def assemble_file(name):
    """Возвращает промежуточное представление примера."""
    return parse((EXAMPLES / name).read_text(encoding="utf-8"))


class AssemblerTest(unittest.TestCase):
    """Этап 1: разбор языка ассемблера."""

    def test_spec_fields(self):
        """Поля A и B совпадают с тестами спецификации."""
        fields = [(cmd["A"], cmd["B"]) for cmd in assemble_file("spec.csv")]
        self.assertEqual(fields, [(119, 668), (16, 786), (89, 687), (38, 252)])

    def test_number_formats(self):
        """Операнд можно записать в десятичной, 16- и 2-ичной форме."""
        program = parse("load,0x29C\nload,0b1010\nLOAD, 7\n")
        self.assertEqual([cmd["B"] for cmd in program], [668, 10, 7])

    def test_limits(self):
        """Граничные значения поля B проходят."""
        program = parse("load,32767\nread,16383\nwrite,4095\neq,4095\n")
        self.assertEqual(len(program), 4)

    def test_errors(self):
        """Ошибочные программы отклоняются."""
        for path in sorted((EXAMPLES / "errors").glob("*.csv")):
            with self.subTest(path.name), self.assertRaises(SystemExit):
                parse(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
