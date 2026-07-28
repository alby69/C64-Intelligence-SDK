#!/usr/bin/env python3
"""Wrapper: disk-tools plugin -> editor/diskimage.py + petscii converter."""

import os
import sys
import shutil

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SDK_ROOT, "editor"))


def get_diskimage():
    try:
        from readycode_py.diskimage import C64DiskImage
        return C64DiskImage(), None
    except ImportError as e:
        return None, str(e)


def cmd_list(args):
    if not args:
        print("[ERROR] Specifica un'immagine disco (.d64/.d81)")
        return 1
    image_path = args[0]
    if not os.path.isfile(image_path):
        print(f"[ERROR] File non trovato: {image_path}")
        return 1

    disk, err = get_diskimage()
    if disk:
        try:
            entries = disk.list_files(image_path)
            if entries:
                print(f"[OK] Contenuto di {os.path.basename(image_path)}:")
                print(f"[PRG] {'Nome':18s} {'Tipo':6s} {'Dimensione':>10s}")
                print(f"[PRG] {'-'*18} {'-'*6} {'-'*10}")
                for e in entries:
                    name = e.get("name", "?")
                    ftype = e.get("type", "?")
                    size = e.get("size", 0)
                    print(f"[BASIC] {name:18s} {ftype:6s} {size:>10d}")
            else:
                print(f"[C64] Disco vuoto o non leggibile")
        except Exception as e:
            print(f"[ERROR] Lettura disco fallita: {e}")
    else:
        print(f"[C64] diskimage.py non disponibile, uso fallback run_c64.py")
        import subprocess
        r = subprocess.run(
            [sys.executable, os.path.join(SDK_ROOT, "run_c64.py"), "disk", "list", image_path],
            capture_output=True, text=True, cwd=SDK_ROOT
        )
        if r.stdout:
            print(r.stdout)
        if r.returncode != 0:
            print(f"[ERROR] {r.stderr}")

    return 0


def cmd_inject(args):
    if len(args) < 2:
        print("[ERROR] Uso: inject <image.d64> <file>")
        return 1
    image_path, file_path = args[0], args[1]
    if not os.path.isfile(image_path):
        print(f"[ERROR] Disco non trovato: {image_path}")
        return 1
    if not os.path.isfile(file_path):
        print(f"[ERROR] File non trovato: {file_path}")
        return 1

    disk, err = get_diskimage()
    if disk:
        try:
            disk.add_file(image_path, file_path)
            print(f"[OK] {os.path.basename(file_path)} inserito in {os.path.basename(image_path)}")
        except Exception as e:
            print(f"[ERROR] Inserimento fallito: {e}")
    else:
        import subprocess
        r = subprocess.run(
            [sys.executable, os.path.join(SDK_ROOT, "run_c64.py"), "disk", "inject", image_path, file_path],
            capture_output=True, text=True, cwd=SDK_ROOT
        )
        if r.stdout:
            print(r.stdout)
        if r.returncode != 0:
            print(f"[ERROR] {r.stderr}")
    return 0


def cmd_extract(args):
    if len(args) < 2:
        print("[ERROR] Uso: extract <image.d64> <name> [-o <output>]")
        return 1
    image_path, name = args[0], args[1]
    output = None
    for i, a in enumerate(args):
        if a in ("-o", "--output") and i + 1 < len(args):
            output = args[i + 1]

    if not os.path.isfile(image_path):
        print(f"[ERROR] Disco non trovato: {image_path}")
        return 1

    if not output:
        output = name

    disk, err = get_diskimage()
    if disk:
        try:
            disk.extract_file(image_path, name, output)
            sz = os.path.getsize(output) if os.path.isfile(output) else 0
            print(f"[OK] {name} estratto -> {output} ({sz}B)")
        except Exception as e:
            print(f"[ERROR] Estrazione fallita: {e}")
    else:
        import subprocess
        cmd = [sys.executable, os.path.join(SDK_ROOT, "run_c64.py"), "disk", "extract", image_path, name]
        if output:
            cmd.extend(["-o", output])
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=SDK_ROOT)
        if r.stdout:
            print(r.stdout)
        if r.returncode != 0:
            print(f"[ERROR] {r.stderr}")
    return 0


def cmd_create(args):
    output = None
    fmt = "d64"
    label = "UNTITLED"
    for i, a in enumerate(args):
        if a in ("-o", "--output") and i + 1 < len(args):
            output = args[i + 1]
        if a == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
        if a == "--label" and i + 1 < len(args):
            label = args[i + 1]

    if not output:
        print("[ERROR] Specifica --output <path>")
        return 1

    disk, err = get_diskimage()
    if disk:
        try:
            disk.create_new(output, fmt=fmt, name=label)
            sz = os.path.getsize(output) if os.path.isfile(output) else 0
            print(f"[OK] Disco {fmt.upper()} creato: {output} ({sz}B)")
            print(f"[OK] Label: {label}")
        except Exception as e:
            print(f"[ERROR] Creazione disco fallita: {e}")
    else:
        import subprocess
        r = subprocess.run(
            [sys.executable, os.path.join(SDK_ROOT, "run_c64.py"), "disk", "create", label, "-o", output, "--format", fmt],
            capture_output=True, text=True, cwd=SDK_ROOT
        )
        if r.stdout:
            print(r.stdout)
        if r.returncode != 0:
            print(f"[ERROR] {r.stderr}")
    return 0


def cmd_format(args):
    if not args:
        print("[ERROR] Specifica un'immagine disco")
        return 1
    image_path = args[0]
    label = "UNTITLED"
    for i, a in enumerate(args):
        if a == "--label" and i + 1 < len(args):
            label = args[i + 1]

    disk, err = get_diskimage()
    if disk:
        try:
            disk.format(image_path, name=label)
            print(f"[OK] Disco formattato: {os.path.basename(image_path)} ({label})")
        except Exception as e:
            print(f"[ERROR] Formattazione fallita: {e}")
    else:
        print("[ERROR] diskimage.py non disponibile per formattazione diretta")
    return 0


def cmd_prg_to_disk(args):
    if not args:
        print("[ERROR] Specifica percorso output")
        return 1
    output = args[0]

    files_str = None
    label = "PROGRAMS"
    for i, a in enumerate(args):
        if a == "--files" and i + 1 < len(args):
            files_str = args[i + 1]
        if a == "--label" and i + 1 < len(args):
            label = args[i + 1]

    if not files_str:
        print("[ERROR] Specifica --files file1.prg,file2.prg,...")
        return 1

    files = [f.strip() for f in files_str.split(",")]

    disk, err = get_diskimage()
    if disk:
        try:
            disk.create_new(output, fmt="d64", name=label)
            for f in files:
                if os.path.isfile(f):
                    disk.add_file(output, f)
                    print(f"[OK] Aggiunto: {f}")
                else:
                    print(f"[C64] File non trovato: {f}")
            print(f"[OK] Disco creato: {output} con {len([f for f in files if os.path.isfile(f)])} file")
        except Exception as e:
            print(f"[ERROR] {e}")
    else:
        print("[ERROR] diskimage.py non disponibile")
    return 0


def cmd_petscii_convert(args):
    if len(args) < 2:
        print("[ERROR] Uso: petscii-convert <input> <direction>")
        print("[C64] direction: to-petscii|to-ascii")
        return 1
    input_path, direction = args[0], args[1]
    output = None
    for i, a in enumerate(args):
        if a in ("-o", "--output") and i + 1 < len(args):
            output = args[i + 1]

    if not os.path.isfile(input_path):
        print(f"[ERROR] File non trovato: {input_path}")
        return 1

    if not output:
        base, ext = os.path.splitext(input_path)
        output = f"{base}_{'petscii' if direction == 'to-petscii' else 'ascii'}{ext}"

    try:
        from readycode_py.petscii import PETSCIIConverter
        conv = PETSCIIConverter()
        with open(input_path) as f:
            text = f.read()

        if direction == "to-petscii":
            result = conv.ascii_to_petscii(text)
        elif direction == "to-ascii":
            result = conv.petscii_to_ascii(text)
        else:
            print(f"[ERROR] Direzione sconosciuta: {direction}")
            return 1

        with open(output, "w") as f:
            f.write(result)
        print(f"[OK] Convertito {input_path} -> {output} ({len(result)} byte)")
    except ImportError:
        print("[ERROR] PETSCIIConverter non disponibile (pip install -e editor)")
        return 1
    except Exception as e:
        print(f"[ERROR] Conversione fallita: {e}")
        return 1
    return 0


def main():
    if len(sys.argv) < 2:
        print("[ERROR] Comando richiesto: list|inject|extract|create|format|prg-to-disk|petscii-convert")
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "list": cmd_list,
        "inject": cmd_inject,
        "extract": cmd_extract,
        "create": cmd_create,
        "format": cmd_format,
        "prg-to-disk": cmd_prg_to_disk,
        "petscii-convert": cmd_petscii_convert,
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
