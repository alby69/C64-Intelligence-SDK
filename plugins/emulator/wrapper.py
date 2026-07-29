#!/usr/bin/env python3
"""Wrapper: emulator plugin -> c64py + VICE monitor via editor/readycode_py/vice_client.py."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SDK_ROOT, "editor"))

_vice = None


def _get_vice_path() -> str:
    """Read VICE path from user settings (set via UI preferences)."""
    settings_file = Path(SDK_ROOT) / "config" / "settings.json"
    if settings_file.exists():
        try:
            data = json.loads(settings_file.read_text())
            path = data.get("VICE_path")
            if path and os.path.isfile(path):
                return path
        except (json.JSONDecodeError, OSError):
            pass
    return "x64sc"


def cmd_run(args):
    """Run in c64py emulator (existing functionality)."""
    if not args:
        print("[ERROR] Specifica un file .c64 o .prg")
        return 1
    input_path = args[0]

    sid = "--sid" in args
    resid = "--resid" in args
    timeout = 30
    for i, a in enumerate(args):
        if a == "--timeout" and i + 1 < len(args):
            timeout = int(args[i + 1])

    print(f"[OK] Avvio c64py: {os.path.basename(input_path)}")
    print(
        f"[C64] SID={'on' if sid else 'off'} reSID={'on' if resid else 'off'} timeout={timeout}s"
    )

    import subprocess

    cmd = [sys.executable, os.path.join(SDK_ROOT, "run_c64.py"), "run", input_path]
    if sid:
        cmd.append("--sid")
    if resid:
        cmd.append("--resid")
    if timeout:
        cmd.append("--timeout")
        cmd.append(str(timeout))

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.stdout:
            print(r.stdout)
        if r.stderr:
            print(f"[C64] {r.stderr[:500]}")
        if r.returncode == 0:
            print("[OK] Esecuzione completata")
        else:
            print(f"[ERROR] Exit code: {r.returncode}")
    except subprocess.TimeoutExpired:
        print(f"[C64] Timeout ({timeout}s) — esecuzione terminata")
    except Exception as e:
        print(f"[ERROR] {e}")
    return 0


def _get_vice_bridge(host="127.0.0.1", port=6510):
    try:
        sys.path.insert(0, os.path.join(SDK_ROOT, "debugger"))
        from c64debugger.vice_bridge import VICERemoteMonitorBridge

        return VICERemoteMonitorBridge(host, port)
    except ImportError:
        return None


def cmd_vice_run(args):
    """Run PRG in VICE headless with monitor."""
    if not args:
        print("[ERROR] Specifica un file .prg")
        return 1
    prg_path = args[0]
    if not os.path.isfile(prg_path):
        print(f"[ERROR] File non trovato: {prg_path}")
        return 1

    headless = "--headless" in args
    limit_cycles = 10000000
    for i, a in enumerate(args):
        if a == "--limit-cycles" and i + 1 < len(args):
            limit_cycles = int(args[i + 1])

    bridge = _get_vice_bridge()
    if bridge:
        print(f"[OK] Avvio VICE con {os.path.basename(prg_path)}")
        if bridge.start_vice_headless(prg_path, limit_cycles=limit_cycles):
            print(f"[OK] VICE avviato")
            global _vice
            _vice = bridge
        else:
            print("[ERROR] Avvio VICE fallito")
            return 1
    else:
        print("[C64] Fallback: avvio VICE manuale")
        vice_exe = _get_vice_path()
        cmd = [vice_exe, "-monitorport", "6510", prg_path]
        if headless:
            cmd.insert(1, "-headless")
        try:
            subprocess.Popen(cmd)
            print(f"[OK] VICE avviato: {' '.join(cmd)}")
        except FileNotFoundError:
            print(f"[ERROR] VICE ({vice_exe}) non trovato")
            return 1
    return 0


def cmd_vice_attach(args):
    host = "127.0.0.1"
    port = 6510
    for i, a in enumerate(args):
        if a == "--host" and i + 1 < len(args):
            host = args[i + 1]
        if a == "--port" and i + 1 < len(args):
            port = int(args[i + 1])

    bridge = _get_vice_bridge(host, port)
    if bridge:
        ok, msg = bridge.connect()
        if ok:
            global _vice
            _vice = bridge
            print(f"[OK] Connesso a VICE su {host}:{port}")
        else:
            print(f"[ERROR] Connessione fallita: {msg}")
            return 1
    else:
        print("[ERROR] ViceBridge non disponibile")
        return 1
    return 0


def ensure_vice():
    global _vice
    if _vice is None:
        bridge = _get_vice_bridge()
        if bridge:
            try:
                bridge.connect()
                _vice = bridge
            except Exception as e:
                print(f"[ERROR] Connessione a VICE fallita: {e}")
                return None
        else:
            print("[ERROR] ViceBridge non disponibile")
            return None
    return _vice


def cmd_vice_step(args):
    client = ensure_vice()
    if not client:
        return 1
    try:
        result = client.send_command("s")
        print("[OK] Step eseguito")
        if result:
            print(f"[C64] {result}")
    except Exception as e:
        print(f"[ERROR] Step: {e}")
    return 0


def cmd_vice_reset(args):
    client = ensure_vice()
    if not client:
        return 1
    try:
        client.kill_vice()
        print("[OK] VICE arrestato")
    except Exception as e:
        print(f"[ERROR] Reset: {e}")
    return 0


def cmd_vice_memory(args):
    client = ensure_vice()
    if not client:
        return 1
    if not args:
        print("[ERROR] Specifica un indirizzo")
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
        data = client.read_memory(addr_int, addr_int + size)
        if data:
            print(f"[OK] Memoria da ${addr_int:04X} ({size} byte):")
            for offset in range(0, len(data), 16):
                chunk = data[offset : offset + 16]
                hex_part = " ".join(f"{b:02x}" for b in chunk)
                ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
                print(f"  ${addr_int + offset:04X}: {hex_part:48s}  {ascii_part}")
    except Exception as e:
        print(f"[ERROR] Lettura memoria: {e}")
    return 0


def cmd_vice_registers(args):
    client = ensure_vice()
    if not client:
        return 1
    try:
        regs = client.get_registers()
        if regs:
            print("[OK] Registri CPU 6502 (da VICE):")
            for k, v in regs.items():
                if isinstance(v, int):
                    print(
                        f"  {k:4s} = ${v:04X}" if v > 0xFF else f"  {k:4s} = ${v:02X}"
                    )
                else:
                    print(f"  {k:4s} = {v}")
    except Exception as e:
        print(f"[ERROR] Lettura registri: {e}")
    return 0


def cmd_vice_info(args):
    print("[C64] Info VICE: usa 'vice-registers' per vedere i registri CPU")
    print("[C64] Per la versione VICE, esegui: x64sc --version")
    return 0


def cmd_vice_upload(args):
    client = ensure_vice()
    if not client:
        return 1
    if not args:
        print("[ERROR] Specifica un file .prg")
        return 1
    prg_path = args[0]
    if not os.path.isfile(prg_path):
        print(f"[ERROR] File non trovato: {prg_path}")
        return 1

    address = "0x0801"
    for i, a in enumerate(args):
        if a == "--address" and i + 1 < len(args):
            address = args[i + 1]

    if address.startswith("0x"):
        addr_int = int(address, 16)
    else:
        addr_int = int(address)

    try:
        with open(prg_path, "rb") as f:
            data = f.read()
        client.write_memory(addr_int, data)
        print(f"[OK] PRG caricato a ${addr_int:04X} ({len(data)} byte)")
    except Exception as e:
        print(f"[ERROR] Upload PRG: {e}")
    return 0


def main():
    if len(sys.argv) < 2:
        print(
            "[ERROR] Comando richiesto: run|vice-run|vice-attach|vice-step|vice-reset|vice-memory|vice-registers|vice-info|vice-upload"
        )
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "run": cmd_run,
        "vice-run": cmd_vice_run,
        "vice-attach": cmd_vice_attach,
        "vice-step": cmd_vice_step,
        "vice-reset": cmd_vice_reset,
        "vice-memory": cmd_vice_memory,
        "vice-registers": cmd_vice_registers,
        "vice-info": cmd_vice_info,
        "vice-upload": cmd_vice_upload,
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
