import sys
import unittest
from pathlib import Path

PRACTICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRACTICE.parent))

from src.uvm_asm import parse, translate

EXAMPLES = PRACTICE / "examples"


def assemble_file(name):
    return parse((EXAMPLES / name).read_text(encoding="utf-8"))


class AssemblerTest(unittest.TestCase):

    def test_spec_fields(self):
        fields = [(cmd["A"], cmd["B"]) for cmd in assemble_file("spec.csv")]
        self.assertEqual(fields, [(119, 668), (16, 786), (89, 687), (38, 252)])

    def test_number_formats(self):
        program = parse("load,0x29C\nload,0b1010\nLOAD, 7\n")
        self.assertEqual([cmd["B"] for cmd in program], [668, 10, 7])

    def test_limits(self):
        program = parse("load,32767\nread,16383\nwrite,4095\neq,4095\n")
        self.assertEqual(len(program), 4)

    def test_errors(self):
        for path in sorted((EXAMPLES / "errors").glob("*.csv")):
            with self.subTest(path.name), self.assertRaises(SystemExit):
                parse(path.read_text(encoding="utf-8"))


class MachineCodeTest(unittest.TestCase):

    def test_spec_bytes(self):
        code = translate(assemble_file("spec.csv"))
        self.assertEqual(code, bytes([
            0x77, 0x4E, 0x01,
            0x10, 0x89, 0x01,
            0xD9, 0x57, 0x01,
            0x26, 0x7E, 0x00,
        ]))

    def test_size(self):
        code = translate(parse("load,1\nload,2\nwrite,3\n"))
        self.assertEqual(len(code), 9)


if __name__ == "__main__":
    unittest.main()
