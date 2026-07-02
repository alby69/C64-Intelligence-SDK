from .sim.sim6502 import sim6502, Flags
from .sim.dis6502 import dis6502

class C64Simulator:
    def __init__(self, prg: bytes = None, symbols=None):
        self.output_buffer = ""
        # C64 uses NMOS 6502
        self.sim = sim6502(variant="NMOS", symbols=symbols)
        self.dis = dis6502(self.sim.memory_map._memory_map, symbols=symbols)
        self.history = []
        self.max_history = 100

        if prg:
            self.load_prg(prg)

    def load_prg(self, prg: bytes):
        if len(prg) < 2:
            return
        load_addr = prg[0] + (prg[1] << 8)
        data = prg[2:]
        self.sim.memory_map.InitializeMemory(load_addr, data)
        self.sim.pc = load_addr

    def step(self):
        pc = self.sim.pc

        # Disassemble for history
        line, length = self.dis.disassemble_line(pc)
        self.history.append({
            "pc": pc,
            "line": line,
            "registers": {
                "a": self.sim.a,
                "x": self.sim.x,
                "y": self.sim.y,
                "sp": self.sim.sp,
                "flags": self.sim.cc
            }
        })
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # Kernal Traps
        if pc == 0xFFD2: # CHROUT
            # Skip disassembly entry for Kernal trap to avoid "brk" showing up
            if self.history:
                self.history.pop()
            char = self.sim.a
            # Convert PETSCII to ASCII roughly for now
            if char == 0x0D:
                self.output_buffer += "\n"
            elif 32 <= char <= 126:
                self.output_buffer += chr(char)

            # RTS
            self.sim.pc = (self.sim.pulladdr() + 1) % 0x10000
            return True

        if pc == 0xFFE4: # GETIN
            # Simulate no key pressed
            self.sim.a = 0
            self.sim.set_z(True)
            self.sim.pc = (self.sim.pulladdr() + 1) % 0x10000
            return True

        try:
            self.sim.execute()
        except Exception as e:
            self.output_buffer += f"\n[Simulation Error: {e}]\n"
            return False

        return True

    def run(self, max_steps=10000):
        steps = 0
        while steps < max_steps:
            pc = self.sim.pc
            # Basic check for end of program (RTS at top level or BRK)
            # Use % 65536 to be safe
            opcode = self.sim.memory_map._memory_map[pc % 65536]

            # Kernal Traps are not real opcodes in our memory map usually
            if pc >= 0xFF00:
                 if not self.step():
                     break
                 steps += 1
                 continue

            if opcode == 0x60 and self.sim.sp == 0xFF: # RTS at start
                break
            if opcode == 0x00: # BRK
                break

            if not self.step():
                break
            steps += 1
        return steps
