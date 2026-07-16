# c64validator shared library

from pyc64c.sim.sim6502 import sim6502
from pyc64c.sim.dis6502 import Dis6502

class C64Validator:
    """Validator class to run simulation steps and check 6502 program correctness."""
    def __init__(self, prg_bytes: bytes, load_address: int = 0x0801):
        self.sim = sim6502(object_code=prg_bytes, address=load_address)
        self.sim.reset()

    def run_steps(self, steps: int = 100):
        for _ in range(steps):
            res = self.sim.execute()
            if res and res[0] in ("not_instruction", "weeds"):
                return False, f"CPU crashed/invalid opcode at PC=${self.sim.pc:04X}"
        return True, "Success"
