import unittest
import json
from pyc64c.compiler import compile_source, compile_to_prg

class TestNewFeatures(unittest.TestCase):
    def test_text_color_builtin(self):
        src = "def main():\n    text_color(5)"
        res = compile_source(src)
        self.assertTrue(res.success)
        # We can't easily check the machine code here without a disassembler,
        # but we can check if it compiles.
        prg, res = compile_to_prg(src)
        self.assertIsNotNone(prg)

    def test_poke16_peek16(self):
        src = """
def main():
    poke16(0x0400, 0x1234)
    x: word = peek16(0x0400)
"""
        res = compile_source(src)
        self.assertTrue(res.success)
        prg, res = compile_to_prg(src)
        self.assertIsNotNone(prg)

    def test_16bit_assignment_and_addition(self):
        src = """
def main():
    x: word = 1000
    x = x + 500
    y: word = x
"""
        res = compile_source(src)
        self.assertTrue(res.success)
        prg, res = compile_to_prg(src)
        self.assertIsNotNone(prg)

    def test_optimizer_folding(self):
        src = """
def main():
    x: byte = 2 + 2 * 3
    if 10 > 5 and 3 < 4:
        print("ok")
"""
        res = compile_source(src)
        self.assertTrue(res.success)
        # Check if constant folding worked by looking at the AST
        # 2 + 2 * 3 = 8
        found_8 = False
        def walk(node):
            nonlocal found_8
            if isinstance(node, dict):
                if node.get('k') == 'Literal' and node.get('value') == 8:
                    found_8 = True
                for v in node.values():
                    if isinstance(v, (dict, list)):
                        walk(v)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(res.ast)
        self.assertTrue(found_8, "Constant folding failed to produce 8")

    def test_kernal_builtins(self):
        src = "def main():\n    kernal_chrout(65)\n    c: byte = kernal_chrin()"
        res = compile_source(src)
        self.assertTrue(res.success)
        prg, res = compile_to_prg(src)
        self.assertIsNotNone(prg)

if __name__ == '__main__':
    unittest.main()
