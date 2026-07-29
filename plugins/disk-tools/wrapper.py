#!/usr/bin/env python3
"""Wrapper: disk-tools plugin -> editor/diskimage.py + petscii converter."""

import os
import sys
import shutil

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SDK_ROOT, "editor"))

try:
    from readycode_py.diskimage import DiskImage, DiskGeometry, C64UFileKind
except ImportError:
    C64UFileKind = None


def get_diskimage(fmt="d64"):
    try:
        from readycode_py.diskimage import DiskImage, DiskGeometry, C64UFileKind

        geo = DiskGeometry.D64 if fmt == "d64" else DiskGeometry.D81
        return DiskImage(geo), None
    except Exception as e:
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
            with open(image_path, "rb") as f:
                image_data = f.read()
            entries = disk.read_directory(image_data)
            if entries:
                print(f"[OK] Contenuto di {os.path.basename(image_path)}:")
                print(f"[PRG] {'Nome':18s} {'Tipo':6s} {'Dimensione':>10s}")
                print(f"[PRG] {'-' * 18} {'-' * 6} {'-' * 10}")
                for e in entries:
                    print(
                        f"[BASIC] {e.name:18s} {e.kind.name:6s} {len(e.content):>10d}"
                    )
            else:
                print(f"[C64] Disco vuoto o non leggibile")
        except Exception as e:
            print(f"[ERROR] Lettura disco fallita: {e}")
    else:
        print(f"[C64] diskimage.py non disponibile, uso fallback run_c64.py")
        import subprocess

        r = subprocess.run(
            [
                sys.executable,
                os.path.join(SDK_ROOT, "run_c64.py"),
                "disk",
                "list",
                image_path,
            ],
            capture_output=True,
            text=True,
            cwd=SDK_ROOT,
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
            with open(image_path, "rb") as f:
                image_data = f.read()
            with open(file_path, "rb") as f:
                file_data = f.read()
            name = os.path.splitext(os.path.basename(file_path))[0]
            new_image = disk.add_entry(image_data, name, C64UFileKind.Prg, file_data)
            with open(image_path, "wb") as f:
                f.write(new_image)
            print(
                f"[OK] {os.path.basename(file_path)} inserito in {os.path.basename(image_path)}"
            )
        except Exception as e:
            print(f"[ERROR] Inserimento fallito: {e}")
    else:
        import subprocess

        r = subprocess.run(
            [
                sys.executable,
                os.path.join(SDK_ROOT, "run_c64.py"),
                "disk",
                "inject",
                image_path,
                file_path,
            ],
            capture_output=True,
            text=True,
            cwd=SDK_ROOT,
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
            with open(image_path, "rb") as f:
                image_data = f.read()
            entries = disk.read_directory(image_data)
            found = None
            for e in entries:
                if e.name.upper() == name.upper():
                    found = e
                    break
            if found:
                with open(output, "wb") as f:
                    f.write(found.content)
                print(f"[OK] {name} estratto -> {output} ({len(found.content)}B)")
            else:
                print(f"[ERROR] File '{name}' non trovato sul disco")
        except Exception as e:
            print(f"[ERROR] Estrazione fallita: {e}")
    else:
        import subprocess

        cmd = [
            sys.executable,
            os.path.join(SDK_ROOT, "run_c64.py"),
            "disk",
            "extract",
            image_path,
            name,
        ]
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

    disk, err = get_diskimage(fmt)
    if disk:
        try:
            blank = disk.create_blank_image(label)
            with open(output, "wb") as f:
                f.write(blank)
            print(f"[OK] Disco {fmt.upper()} creato: {output} ({len(blank)}B)")
            print(f"[OK] Label: {label}")
        except Exception as e:
            print(f"[ERROR] Creazione disco fallita: {e}")
    else:
        import subprocess

        r = subprocess.run(
            [
                sys.executable,
                os.path.join(SDK_ROOT, "run_c64.py"),
                "disk",
                "create",
                label,
                "-o",
                output,
                "--format",
                fmt,
            ],
            capture_output=True,
            text=True,
            cwd=SDK_ROOT,
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
            blank = disk.create_blank_image(label)
            with open(image_path, "wb") as f:
                f.write(blank)
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
            image_data = disk.create_blank_image(label)
            for f in files:
                if os.path.isfile(f):
                    with open(f, "rb") as fh:
                        file_data = fh.read()
                    fname = os.path.splitext(os.path.basename(f))[0]
                    image_data = disk.add_entry(
                        image_data, fname, C64UFileKind.Prg, file_data
                    )
                    print(f"[OK] Aggiunto: {f}")
                else:
                    print(f"[C64] File non trovato: {f}")
            with open(output, "wb") as f:
                f.write(image_data)
            print(
                f"[OK] Disco creato: {output} con {len([f for f in files if os.path.isfile(f)])} file"
            )
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
        print(
            "[ERROR] Comando richiesto: list|inject|extract|create|format|prg-to-disk|petscii-convert"
        )
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
