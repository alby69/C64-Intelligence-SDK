import os
import logging

from .basic_tokens import detokenize_basic, is_basic_prg, hex_dump

log = logging.getLogger("prg")
_C64Disassembler = None
try:
    from pyc64c.sim.dis6502 import Dis6502

    _C64Disassembler = Dis6502
except ImportError:
    try:
        from py65.disassembler import Disassembler

        _C64Disassembler = Disassembler
    except ImportError:
        pass


class PRGFile:
    def __init__(self, data: bytes):
        if len(data) < 2:
            raise ValueError("PRG: file troppo corto")
        self._raw = data
        self._load_addr = data[0] + (data[1] << 8)
        self._prg_data = data[2:]

    @classmethod
    def load(cls, path: str) -> "PRGFile":
        with open(path, "rb") as f:
            return cls(f.read())

    def load_address(self) -> int:
        return self._load_addr

    def data(self) -> bytes:
        return self._prg_data

    def is_basic(self) -> bool:
        return is_basic_prg(self._raw)

    def to_basic(self) -> str:
        return detokenize_basic(self._raw)

    def to_asm(self) -> str:
        if self.is_basic() or _C64Disassembler is None:
            return ""
        try:
            if _C64Disassembler.__name__ == "Dis6502":
                dis = _C64Disassembler()
                return dis.disassemble(self._prg_data, self._load_addr)
            else:
                dis = _C64Disassembler()
                lines = []
                addr = self._load_addr
                for opcode, mnemonic, mode in dis.disassemble(self._prg_data):
                    bytes_str = " ".join(f"{b:02X}" for b in opcode)
                    lines.append(f"{addr:04X}  {bytes_str:<8}  {mnemonic}")
                    addr += len(opcode)
                return "\n".join(lines)
        except Exception as e:
            return f"; disassembly failed: {e}"

    def to_hex_dump(self) -> str:
        header = f"; Load address: ${self._load_addr:04X}\n"
        header += f"; Size: {len(self._prg_data)} bytes\n\n"
        return header + hex_dump(self._prg_data)

    def extract(self, output_dir: str) -> list[str]:
        os.makedirs(output_dir, exist_ok=True)
        safe = "prg_output"
        results: list[str] = []

        if self.is_basic():
            source = self.to_basic()
            if source.strip():
                out = os.path.join(output_dir, f"{safe}.bas.txt")
                with open(out, "w") as f:
                    f.write(
                        f"REM BASIC extracted\nREM Load addr: ${self._load_addr:04X}\n\n"
                    )
                    f.write(source)
                log.info(f"  BASIC -> {out}")
                results.append(out)

        ml_path = os.path.join(output_dir, f"{safe}.ml.txt")
        with open(ml_path, "w") as f:
            f.write(self.to_hex_dump())
        log.info(f"  ML dump -> {ml_path}")
        results.append(ml_path)

        if not self.is_basic() and _C64Disassembler:
            asm = self.to_asm()
            if asm:
                asm_path = os.path.join(output_dir, f"{safe}.asm")
                with open(asm_path, "w") as f:
                    f.write(
                        f"; PRG disassembly\n; Load addr: ${self._load_addr:04X}\n\n"
                    )
                    f.write(asm)
                log.info(f"  Disassembly -> {asm_path}")
                results.append(asm_path)

        return results


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m pyc64c.formats.prg <file.prg> [output_dir]")
        sys.exit(1)

    path = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "data/input"
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    prg = PRGFile.load(path)
    print(f"Caricato PRG, load address: ${prg.load_address():04X}")
    print(f"  BASIC: {prg.is_basic()}")
    print(f"  Size: {len(prg.data())} bytes")

    ex = prg.extract(output)
    print(f"\nEstratti {len(ex)} file.")


if __name__ == "__main__":
    main()
