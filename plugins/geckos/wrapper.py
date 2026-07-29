#!/usr/bin/env python3
"""Wrapper: geckos plugin -> GeckOS-NG (6502 multitasking OS)."""

import os
import sys
import subprocess

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GECKOS_DIR = os.path.join(SDK_ROOT, "geckos")


def cmd_build(args):
    clean = "--clean" in args or "-c" in args
    target = "all"
    for i, a in enumerate(args):
        if a == "--target" and i + 1 < len(args):
            target = args[i + 1]

    print(f"[OK] Build GeckOS-NG (target: {target})")

    if clean:
        print("[C64] Pulizia...")
        clean_cmd = ["make", "-C", GECKOS_DIR, "clean"]
        r = subprocess.run(clean_cmd, capture_output=True, text=True, cwd=GECKOS_DIR)
        if r.returncode != 0:
            print(f"[C64] Clean: {r.stdout}")
            print(f"[ERROR] Clean fallito: {r.stderr}")
            return 1

    targets = {
        "all": [],
        "kernel": [],
        "apps": ["apps"],
        "sysapps": ["sysapps"],
    }

    make_targets = targets.get(target, [])
    cmd = ["make", "-C", GECKOS_DIR] + make_targets
    print(f"[C64] Esecuzione: {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=GECKOS_DIR, timeout=120)

    if r.stdout:
        print(f"[C64] {r.stdout[:2000]}")
    if r.returncode != 0:
        print(f"[ERROR] Build fallita (exit {r.returncode})")
        if r.stderr:
            print(f"[ERROR] {r.stderr[:500]}")
        return 1

    # Check output files
    dist_dir = os.path.join(GECKOS_DIR, "dist")
    if os.path.isdir(dist_dir):
        outputs = os.listdir(dist_dir)
        print(f"[OK] Build completata ({len(outputs)} file in dist/)")
        for f in sorted(outputs):
            fp = os.path.join(dist_dir, f)
            sz = os.path.getsize(fp)
            print(f"[PRG]  {f:40s} {sz}B")
    else:
        print("[OK] Build completata")

    return 0


def cmd_deploy(args):
    if not args:
        print("[ERROR] Specifica percorso output (es. geckos.d64)")
        return 1
    output_path = args[0]
    fmt = "d64"
    for i, a in enumerate(args):
        if a == "--format" and i + 1 < len(args):
            fmt = args[i + 1]

    print(f"[OK] Deploy GeckOS su {output_path} (formato: {fmt})")

    dist_dir = os.path.join(GECKOS_DIR, "dist")
    if not os.path.isdir(dist_dir):
        print("[ERROR] Esegui prima 'geckos build'. dist/ non trovato.")
        return 1

    # Use diskimage.py from editor/ if available
    try:
        sys.path.insert(0, os.path.join(SDK_ROOT, "editor"))
        from readycode_py.diskimage import C64DiskImage

        img = C64DiskImage()
        img.create_new(output_path, fmt=fmt, name="GECKOS-NG")
        for f in sorted(os.listdir(dist_dir)):
            fp = os.path.join(dist_dir, f)
            if os.path.isfile(fp):
                img.add_file(fp, f)
        print(f"[OK] Disco creato con {len(os.listdir(dist_dir))} file")
    except ImportError:
        print("[C64] diskimage.py non disponibile, copio solo i file binari")
        import shutil

        bin_dir = os.path.join(GECKOS_DIR, "os", "bin")
        os.makedirs(output_path, exist_ok=True)
        if os.path.isdir(bin_dir):
            for f in os.listdir(bin_dir):
                shutil.copy2(os.path.join(bin_dir, f), os.path.join(output_path, f))
        if os.path.isdir(dist_dir):
            for f in os.listdir(dist_dir):
                shutil.copy2(os.path.join(dist_dir, f), os.path.join(output_path, f))
        print(f"[OK] {len(os.listdir(output_path))} file copiati in {output_path}")

    return 0


def cmd_run(args):
    disk = None
    for i, a in enumerate(args):
        if a == "--disk" and i + 1 < len(args):
            disk = args[i + 1]

    print("[OK] Avvio emulatore con GeckOS")

    if disk and os.path.isfile(disk):
        cmd = ["x64sc", "-autostartprgmode", "0", "-autostartdiskimage", disk]
    else:
        # Look for .d64 in dist/
        dist_dir = os.path.join(GECKOS_DIR, "dist")
        if os.path.isdir(dist_dir):
            d64_files = [f for f in os.listdir(dist_dir) if f.endswith(".d64")]
            if d64_files:
                disk = os.path.join(dist_dir, d64_files[0])
                cmd = ["x64sc", "-autostartdiskimage", disk]
            else:
                cmd = ["x64sc"]
        else:
            cmd = ["x64sc"]

    print(f"[C64] {' '.join(cmd)}")
    try:
        subprocess.Popen(cmd, cwd=SDK_ROOT)
        print(f"[OK] Emulatore avviato")
    except FileNotFoundError:
        print("[ERROR] VICE (x64sc) non trovato. Installa VICE.")
    return 0


def cmd_status(args):
    print("[OK] Stato GeckOS-NG")

    dist_dir = os.path.join(GECKOS_DIR, "dist")
    if os.path.isdir(dist_dir):
        files = os.listdir(dist_dir)
        total_sz = sum(
            os.path.getsize(os.path.join(dist_dir, f))
            for f in files
            if os.path.isfile(os.path.join(dist_dir, f))
        )
        print(f"[OK] dist/: {len(files)} file ({total_sz // 1024}KB)")
        for f in sorted(files):
            fp = os.path.join(dist_dir, f)
            sz = os.path.getsize(fp)
            print(f"[PRG]  {f:40s} {sz}B")
    else:
        print(f"[C64] dist/: assente (esegui 'geckos build')")

    for subdir, label in [
        ("kernel", "Kernel"),
        ("os", "OS bin"),
        ("arch", "Arch"),
        ("include", "Include"),
    ]:
        full = os.path.join(GECKOS_DIR, subdir)
        if os.path.isdir(full):
            n = len(os.listdir(full))
            print(f"[OK] {subdir}/: {n} file")

    # Check build tools
    for tool in ["acme", "xa", "make"]:
        try:
            r = subprocess.run(
                ["where", tool] if os.name == "nt" else ["which", tool],
                capture_output=True,
                text=True,
            )
            if r.returncode == 0:
                print(f"[OK] {tool}: trovato")
            else:
                print(f"[C64] {tool}: non installato")
        except FileNotFoundError:
            print(f"[C64] {tool}: non installato")

    return 0


def main():
    if len(sys.argv) < 2:
        print("[ERROR] Comando richiesto: build|deploy|run|status")
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "build": cmd_build,
        "deploy": cmd_deploy,
        "run": cmd_run,
        "status": cmd_status,
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
