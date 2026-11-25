import sys
import unittest
from pathlib import Path

PRACTICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRACTICE.parent))

from src.uvm_asm import parse, translate
from src.uvm_vm import Machine

EXAMPLES = PRACTICE / "examples"


def assemble_file(name):
    return parse((EXAMPLES / name).read_text(encoding="utf-8"))


def run_source(text):
    machine = Machine(translate(parse(text)))
    machine.run()
    return machine


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


class InterpreterTest(unittest.TestCase):

    def test_copy_array(self):
        text = (EXAMPLES / "copy.csv").read_text(encoding="utf-8")
        memory = run_source(text).memory
        source = [5, 17, 42, 0, 1000, 32767, 3, 8]
        self.assertEqual(memory[1000:1008], source)
        self.assertEqual(memory[1010:1018], source)

    def test_read_offset(self):
        machine = run_source("load,77\nwrite,30\nload,10\nread,20\n")
        self.assertEqual(machine.stack, [77])

    def test_shared_memory(self):
        machine = run_source("load,668\n")
        self.assertEqual(machine.memory[:3], [0x77, 0x4E, 0x01])

    def test_empty_stack(self):
        with self.assertRaises(SystemExit):
            run_source("write,100\n")


class AluTest(unittest.TestCase):

    def test_eq_program(self):
        text = (EXAMPLES / "eq.csv").read_text(encoding="utf-8")
        memory = run_source(text).memory
        self.assertEqual(memory[1010:1017], [1, 0, 1, 1, 0, 0, 1])

    def test_eq_stack(self):
        machine = run_source(
            "load,5\nwrite,100\nload,1\nload,5\neq,100\n"
        )
        self.assertEqual(machine.stack, [1, 1])


class VectorTaskTest(unittest.TestCase):

    def check(self, name, first, second):
        text = (EXAMPLES / name).read_text(encoding="utf-8")
        memory = run_source(text).memory
        expected = [int(a == b) for a, b in zip(first, second)]
        self.assertEqual(memory[1000:1010], first)
        self.assertEqual(memory[1010:1020], expected)

    def test_mixed(self):
        self.check(
            "vectors1.csv",
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            [1, 0, 3, 0, 5, 0, 7, 0, 9, 0],
        )

    def test_equal(self):
        data = [0, 7, 7, 100, 4095, 32767, 12, 0, 1, 500]
        self.check("vectors2.csv", data, data)

    def test_boundaries(self):
        self.check(
            "vectors3.csv",
            [0, 32767, 4095, 1, 0, 255, 256, 1000, 2, 9],
            [0, 32766, 4095, 0, 1, 255, 255, 1000, 3, 9],
        )


if __name__ == "__main__":
    unittest.main()
