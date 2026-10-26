import sys
import os

# Aggiunge il path delle lib interne
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "libs")))

from .py6502.asm6502 import asm6502
from .py6502.sim6502 import sim6502
from .py6502.dis6502 import dis6502

class C64Py6502Adapter:
    """
    Adapter per il simulatore py6502 configurato per Commodore 64.
    """
    def __init__(self):
        self.asm = asm6502()
        self.sim = None
        self.dis = None
        self.symbols = {}

    def assemble(self, code_lines):
        """Assembra il codice e restituisce oggetto e simboli."""
        if isinstance(code_lines, str):
            code_lines = code_lines.splitlines()

        # Gestione automatica ORG se manca
        has_org = any(line.strip().upper().startswith("ORG") for line in code_lines if line.strip())
        if not has_org:
            code_lines.insert(0, " ORG $C000")

        lst, sym_list = self.asm.assemble(code_lines)
        # sym_list è una lista di stringhe per la stampa, noi vogliamo il dizionario interno
        self.symbols = self.asm.symbols
        return self.asm.object_code[:], self.asm.symbols

    def run_simulation(self, object_code, symbols=None, steps=1000, start_addr=None):
        """Esegue una simulazione del codice fornito."""
        if symbols is None:
            symbols = self.symbols

        self.sim = sim6502(object_code, symbols=symbols)
        self.dis = dis6502(object_code, symbols=symbols)

        if start_addr:
            self.sim.pc = start_addr
        else:
            # Se non specificato, prova a usare il reset vector
            if not self.sim.reset():
                # Se non c'è vettore di reset, usiamo $C000
                self.sim.pc = 0xC000

        history = []
        for _ in range(steps):
            pc_before = self.sim.pc
            instr, length = self.dis.disassemble_line(pc_before)

            # Controlla se siamo in un loop infinito o RTS finale
            if object_code[pc_before] == 0x60: # RTS
                history.append(f"{instr.ljust(30)} [RTS - Terminating]")
                break

            try:
                self.sim.execute()
            except Exception as e:
                history.append(f"Error at {pc_before:04X}: {e}")
                break

            state = f"A:{self.sim.a:02X} X:{self.sim.x:02X} Y:{self.sim.y:02X} SP:{self.sim.sp:02X} Flags:{self.sim.cc:02X}"
            history.append(f"{instr.ljust(30)} {state}")

            # Se torniamo allo stesso PC senza cambiare stato (BEQ * etc), fermiamo
            if self.sim.pc == pc_before:
                history.append("... Infinite loop detected ...")
                break

        return history

    def disassemble_prg(self, prg_data):
        """Disassembla un intero file PRG (primi 2 byte sono load address)."""
        if len(prg_data) < 2:
            return "PRG too short"

        load_addr = prg_data[0] + (prg_data[1] << 8)
        code = prg_data[2:]

        # Popola una mappa di memoria vuota
        mem = [-1] * 65536
        for i, byte in enumerate(code):
            if load_addr + i < 65536:
                mem[load_addr + i] = byte

        dis = dis6502(mem)
        # Prima passata per generare simboli
        list(dis.disassemble_region(load_addr, len(code), gen_symbols=True))
        dis.build_symbols_xref()

        # Seconda passata per l'output
        output = []
        output.append(f"; Disassembled from PRG")
        output.append(f"; Load Address: ${load_addr:04X}")
        output.append("")

        lines = dis.disassemble_region(load_addr, len(code))
        for line in lines:
            output.append(line)

        return "\n".join(output)
