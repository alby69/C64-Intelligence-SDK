#!/usr/bin/env python3
"""Wrapper: debugger plugin -> c64debugger (VICE monitor bridge + debugger core)."""

import os
import sys
import time
import re

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SDK_ROOT, "debugger"))

_connection = None  # (bridge, core) tuple


def ensure_connection(args=None):
    global _connection
    if _connection is not None:
        return _connection

    host = "127.0.0.1"
    port = 6510
    if args:
        for i, a in enumerate(args):
            if a == "--host" and i + 1 < len(args):
                host = args[i + 1]
            if a == "--port" and i + 1 < len(args):
                port = int(args[i + 1])

    try:
        from c64debugger.vice_bridge import VICERemoteMonitorBridge
        from c64debugger.debugger_core import C64DebuggerCore

        bridge = VICERemoteMonitorBridge(host, port)
        ok, msg = bridge.connect()
        if not ok:
            print(f"[ERROR] Connessione a VICE monitor su {host}:{port} fallita: {msg}")
            sys.exit(1)
        core = C64DebuggerCore()
        _connection = (bridge, core)
        print(f"[OK] Connesso a VICE monitor su {host}:{port}")
        return _connection
    except ImportError as e:
        print(f"[ERROR] Modulo debugger non trovato: {e}")
        sys.exit(1)


def cmd_attach(args):
    ensure_connection(args)
    return 0


def cmd_run(args):
    prg_path = args[0] if args else None
    if not prg_path or not os.path.isfile(prg_path):
        print("[ERROR] Specifica un file .prg valido")
        return 1
    timeout = 30
    for i, a in enumerate(args):
        if a == "--timeout" and i + 1 < len(args):
            timeout = int(args[i + 1])

    try:
        from c64debugger.vice_bridge import VICERemoteMonitorBridge

        bridge = VICERemoteMonitorBridge()
        if bridge.start_vice_headless(prg_path, limit_cycles=timeout * 1000000):
            print(f"[OK] VICE avviato con {prg_path}")
            time.sleep(2)
            ok, msg = bridge.connect()
            if ok:
                print("[OK] Connesso al monitor VICE")
                global _connection
                from c64debugger.debugger_core import C64DebuggerCore

                _connection = (bridge, C64DebuggerCore())
                print(f"[C64] Esecuzione di {os.path.basename(prg_path)}")
            else:
                print(f"[ERROR] Connessione al monitor VICE fallita: {msg}")
                return 1
        else:
            print("[ERROR] Avvio VICE fallito")
            return 1
    except ImportError:
        print("[ERROR] VICE non trovato. Installa VICE e riprova.")
        return 1
    return 0


def cmd_step(args):
    bridge, core = ensure_connection()
    try:
        result = bridge.send_command("s")
        print(f"[OK] Step eseguito")
        if result:
            print(f"[C64] {result}")
        # Show registers
        regs = bridge.get_registers()
        if regs:
            pc = regs.get("PC", "????")
            a = regs.get("A", "??")
            x = regs.get("X", "??")
            y = regs.get("Y", "??")
            sp = regs.get("SP", "??")
            print(f"[LOAD] PC=${pc} A=${a} X=${x} Y=${y} SP=${sp}")
    except Exception as e:
        print(f"[ERROR] Step fallito: {e}")
    return 0


def cmd_continue(args):
    bridge, core = ensure_connection()
    try:
        result = bridge.send_command("c")
        print(f"[OK] Esecuzione ripresa")
        if result:
            print(f"[C64] {result}")
    except Exception as e:
        print(f"[ERROR] Continue fallito: {e}")
    return 0


def cmd_breakpoint(args):
    bridge, core = ensure_connection()
    if not args:
        print("[ERROR] Specifica un indirizzo (es. $C000 o 49152)")
        return 1

    addr = args[0]
    if addr.startswith("$"):
        addr_int = int(addr[1:], 16)
    else:
        addr_int = int(addr)

    remove = "--remove" in args or "-r" in args

    try:
        if remove:
            core.remove_breakpoint(addr_int)
            print(f"[OK] Breakpoint rimosso a ${addr_int:04X}")
        else:
            core.add_breakpoint(addr_int)
            bridge.set_breakpoint(addr_int)
            print(f"[OK] Breakpoint impostato a ${addr_int:04X}")
    except Exception as e:
        print(f"[ERROR] Breakpoint: {e}")
    return 0


def cmd_registers(args):
    bridge, core = ensure_connection()
    try:
        regs = bridge.get_registers()
        if regs:
            print("[OK] Registri CPU 6502:")
            print(f"  PC = ${regs.get('PC', '????'):04s}  (Program Counter)")
            print(f"  A  = ${regs.get('A', '??'):02s}   (Accumulatore)")
            print(f"  X  = ${regs.get('X', '??'):02s}   (Registro X)")
            print(f"  Y  = ${regs.get('Y', '??'):02s}   (Registro Y)")
            print(f"  SP = ${regs.get('SP', '??'):02s}   (Stack Pointer)")
            sr = regs.get("SR", "??")
            flags = {
                "N": bool(int(sr, 16) & 0x80),
                "V": bool(int(sr, 16) & 0x40),
                "B": bool(int(sr, 16) & 0x10),
                "D": bool(int(sr, 16) & 0x08),
                "I": bool(int(sr, 16) & 0x04),
                "Z": bool(int(sr, 16) & 0x02),
                "C": bool(int(sr, 16) & 0x01),
            }
            flag_str = " ".join(f"{k}={int(v)}" for k, v in flags.items())
            print(f"  SR = ${sr}   ({flag_str})")
        else:
            print("[ERROR] Impossibile leggere registri")
    except Exception as e:
        print(f"[ERROR] Lettura registri: {e}")
    return 0


def cmd_memory(args):
    bridge, core = ensure_connection()
    if not args:
        print("[ERROR] Specifica un indirizzo (es. $C000)")
        return 1
    addr = args[0]
    if addr.startswith("$"):
        addr_int = int(addr[1:], 16)
    else:
        addr_int = int(addr)
    size = 256
    for i, a in enumerate(args):
        if a == "--size" and i + 1 < len(args):
            size = int(args[i + 1])
    try:
        data = bridge.read_memory(addr_int, size)
        if data:
            print(f"[OK] Memoria da ${addr_int:04X} ({size} byte):")
            for offset in range(0, len(data), 16):
                chunk = data[offset : offset + 16]
                hex_part = " ".join(f"{b:02x}" for b in chunk)
                ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
                addr_line = addr_int + offset
                print(f"  ${addr_line:04X}: {hex_part:48s}  {ascii_part}")
        else:
            print("[ERROR] Lettura memoria fallita")
    except Exception as e:
        print(f"[ERROR] Lettura memoria: {e}")
    return 0


def cmd_crash_analyze(args):
    if not args:
        print("[ERROR] Specifica un file crash dump")
        return 1
    dump_path = args[0]
    if not os.path.isfile(dump_path):
        print(f"[ERROR] File non trovato: {dump_path}")
        return 1
    try:
        from c64debugger.debugger_core import C64DebuggerCore

        core = C64DebuggerCore()
        with open(dump_path) as f:
            dump = f.read()
        analysis = core.analyze_crash_dump(dump)
        print(f"[OK] Analisi crash dump completata")
        print(analysis)
    except ImportError:
        print("[ERROR] Debugger core non disponibile")
    except AttributeError:
        print(f"[OK] Dump analizzato: {len(dump)} byte")
        if "stack" in dump.lower():
            print("[LEXER ERROR] Potenziale stack overflow/underflow rilevato")
        if "BRK" in dump or "brk" in dump:
            print("[PARSER ERROR] Istruzione BRK trovata (software break)")
    return 0


def cmd_disassemble(args):
    bridge, core = ensure_connection()
    if not args:
        print("[ERROR] Specifica un indirizzo (es. $C000)")
        return 1
    addr = args[0]
    if addr.startswith("$"):
        addr_int = int(addr[1:], 16)
    else:
        addr_int = int(addr)
    size = 256
    for i, a in enumerate(args):
        if a == "--size" and i + 1 < len(args):
            size = int(args[i + 1])
    try:
        result = bridge.send_command(f"d {addr} {size}")
        if result:
            print(f"[OK] Disassemblato ${addr_int:04X}-${addr_int + size:04X}:")
            print(result)
    except Exception as e:
        print(f"[ERROR] Disassemble: {e}")
    return 0


def cmd_status(args):
    global _connection
    if _connection is None:
        print("[WARN] Debugger non connesso. Usa 'attach' per connetterti a VICE.")
        return 1
    bridge, core = _connection
    try:
        regs = bridge.get_registers()
        if regs:
            pc = regs.get("PC", "????")
            print(f"[OK] Connesso a VICE monitor. PC=${pc}")
        else:
            print("[WARN] Connesso ma nessun registro leggibile")
    except Exception as e:
        print(f"[ERROR] Status: {e}")
    return 0


def cmd_reset(args):
    bridge, core = ensure_connection()
    try:
        bridge.kill_vice()
        print("[OK] Emulatore arrestato (kill)")
    except Exception as e:
        print(f"[ERROR] Reset: {e}")
    return 0


def main():
    if len(sys.argv) < 2:
        print(
            "[ERROR] Comando richiesto: attach|run|step|continue|breakpoint|registers|memory|crash-analyze|disassemble|status|reset"
        )
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "attach": cmd_attach,
        "run": cmd_run,
        "step": cmd_step,
        "continue": cmd_continue,
        "breakpoint": cmd_breakpoint,
        "registers": cmd_registers,
        "memory": cmd_memory,
        "crash-analyze": cmd_crash_analyze,
        "disassemble": cmd_disassemble,
        "status": cmd_status,
        "reset": cmd_reset,
    }

    if command not in commands:
        print(f"[ERROR] Comando sconosciuto: {command}")
        return 1

    try:
        return commands[command](args)
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
