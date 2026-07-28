#!/usr/bin/env python3
"""
readycode CLI — C64 BASIC/tokenizer/disk operations.

Unix-style subcommands for BASIC V2 tokenization, .d64/.d81 disk image
management, minify/prettify transforms, and hardware bridge operations.
"""

import sys
import os
import json
import argparse
import asyncio


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def _write_bytes(path: str, data: bytes):
    with open(path, "wb") as f:
        f.write(data)


def _write_text(path: str, data: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)


# ── tokenize ──────────────────────────────────────────────────────────

def cmd_tokenize(args):
    from .tokenizer import PrgConverter
    source = _read_text(args.input)
    converter = PrgConverter()
    prg = converter.convert_to_prg(source)
    _write_bytes(args.output, prg)
    print(f"[OK] {args.input} → {args.output} ({len(prg)} byte, load $0801)")


# ── detokenize ────────────────────────────────────────────────────────

def cmd_detokenize(args):
    from .tokenizer import PrgConverter
    data = _read_bytes(args.input)
    converter = PrgConverter()
    if not converter.is_basic_program(data):
        print("[WARN] File may not be a valid C64 BASIC program", file=sys.stderr)
    basic = converter.convert_from_prg(data)
    _write_text(args.output, basic)
    print(f"[OK] {args.input} → {args.output}")


# ── disk ──────────────────────────────────────────────────────────────

def _detect_format(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".d81"):
        return "d81"
    return "d64"


def _load_image(path: str) -> bytes:
    data = _read_bytes(path)
    fmt = _detect_format(path)
    expected = 174848 if fmt == "d64" else 819200
    if len(data) != expected:
        print(f"[WARN] Image size {len(data)} bytes (expected {expected})", file=sys.stderr)
    return data


def cmd_disk_list(args):
    from .diskimage import DiskImage, DiskGeometry, C64UFileKind
    data = _load_image(args.image)
    fmt = _detect_format(args.image)
    geo = DiskGeometry.D64 if fmt == "d64" else DiskGeometry.D81
    img = DiskImage(geo)
    entries = img.read_directory(data)

    if args.json:
        out = [{"name": e.name, "type": e.kind.name, "size": len(e.content)} for e in entries]
        print(json.dumps(out, indent=2))
    else:
        if not entries:
            print("(empty disk)")
        else:
            for e in entries:
                kind_tag = {"Prg": "PRG", "Ml": "PRG/ML", "Other": "???"}.get(e.kind.name, e.kind.name)
                print(f"{e.name:<18} {kind_tag:<7} {len(e.content):>6} byte")
        print(f"\n{len(entries)} file(s)")


def cmd_disk_extract(args):
    from .diskimage import DiskImage, DiskGeometry
    data = _load_image(args.image)
    fmt = _detect_format(args.image)
    geo = DiskGeometry.D64 if fmt == "d64" else DiskGeometry.D81
    img = DiskImage(geo)
    entries = img.read_directory(data)
    target = args.name.upper()

    for e in entries:
        if e.name == target:
            out = args.output or f"{e.name}.prg"
            _write_bytes(out, e.content)
            print(f"[OK] {args.image}:{e.name} → {out} ({len(e.content)} byte)")
            return

    print(f"[ERR] '{args.name}' not found on {args.image}", file=sys.stderr)
    sys.exit(1)


def cmd_disk_inject(args):
    from .diskimage import DiskImage, DiskGeometry, C64UFileKind
    data = _load_image(args.image)
    fmt = _detect_format(args.image)
    geo = DiskGeometry.D64 if fmt == "d64" else DiskGeometry.D81
    img = DiskImage(geo)
    content = _read_bytes(args.file)
    name = args.name or os.path.splitext(os.path.basename(args.file))[0]

    new_image = img.add_entry(data, name, C64UFileKind.Prg, content)
    _write_bytes(args.image, new_image)
    print(f"[OK] {args.file} → {args.image}:{name}")


def cmd_disk_create(args):
    from .diskimage import DiskImage, DiskGeometry
    fmt = args.format or "d64"
    geo = DiskGeometry.D64 if fmt == "d64" else DiskGeometry.D81
    img = DiskImage(geo)
    blank = img.create_blank_image(args.name or "UNTITLED")
    _write_bytes(args.output, blank)
    print(f"[OK] Created {fmt.upper()} image: {args.output} ({len(blank)} byte)")


def cmd_disk_delete(args):
    from .diskimage import DiskImage, DiskGeometry
    data = _load_image(args.image)
    fmt = _detect_format(args.image)
    geo = DiskGeometry.D64 if fmt == "d64" else DiskGeometry.D81
    img = DiskImage(geo)
    new_image = img.delete_entry(data, args.name)
    _write_bytes(args.image, new_image)
    print(f"[OK] Deleted '{args.name}' from {args.image}")


def cmd_disk_rename(args):
    from .diskimage import DiskImage, DiskGeometry
    data = _load_image(args.image)
    fmt = _detect_format(args.image)
    geo = DiskGeometry.D64 if fmt == "d64" else DiskGeometry.D81
    img = DiskImage(geo)
    new_image = img.rename_entry(data, args.name, args.new_name)
    _write_bytes(args.image, new_image)
    print(f"[OK] Renamed '{args.name}' → '{args.new_name}' on {args.image}")


# ── minify / prettify ─────────────────────────────────────────────────

def cmd_minify(args):
    from .transform import CodeMinifier
    source = _read_text(args.input)
    result = CodeMinifier.minify(
        source,
        remove_whitespace=not args.keep_whitespace,
        replace_0_with_period=not args.no_period,
        use_scientific_notation=not args.no_scientific,
        remove_comments=not args.keep_comments,
        simplify_next_statements=not args.keep_next_vars,
        renumber_lines=not args.keep_renumber,
    )
    _write_text(args.output, result)
    orig_len = len(source)
    new_len = len(result)
    pct = (1 - new_len / orig_len) * 100 if orig_len > 0 else 0
    print(f"[OK] {args.input} → {args.output} ({orig_len} → {new_len} chars, -{pct:.1f}%)")


def cmd_prettify(args):
    from .transform import CodePrettifier
    source = _read_text(args.input)
    result = CodePrettifier.prettify(
        source,
        add_whitespace=not args.no_whitespace,
        replace_period_with_zero=not args.no_period,
        use_standard_notation=not args.no_scientific,
        add_next_variables=not args.keep_next_vars,
        renumber_lines=not args.no_renumber,
        line_number_increment=args.increment,
        line_number_padding=args.padding,
    )
    _write_text(args.output, result)
    print(f"[OK] {args.input} → {args.output}")


# ── petscii ───────────────────────────────────────────────────────────

def cmd_petscii(args):
    from .petscii import to_screen_code
    value = args.value
    if value.startswith("$"):
        petscii = int(value[1:], 16)
    else:
        petscii = int(value)
    screen = to_screen_code(petscii)
    print(f"PETSCII ${petscii:02X} → Screen Code ${screen:02X} ({screen})")


# ── bridge (C64U / VICE) ─────────────────────────────────────────────

def cmd_bridge_c64u(args):
    from .ultimate_client import C64UltimateClient
    client = C64UltimateClient()

    async def _run():
        if args.action == "run":
            prg = _read_bytes(args.file)
            result = await client.load_prg_async(args.host, prg)
            print(f"[OK] {args.file} loaded on C64U: {result}")
        elif args.action == "list":
            result = await client.list_directory_async(args.host, args.path or "/")
            for entry in result:
                print(json.dumps(entry))
        elif args.action == "mount":
            result = await client.mount_disk_image_async(args.host, args.path)
            print(f"[OK] Mounted: {result}")
        elif args.action == "eject":
            result = await client.eject_disk_image_async(args.host)
            print(f"[OK] Ejected: {result}")

    asyncio.run(_run())


def cmd_bridge_vice(args):
    from .vice_client import ViceClient

    async def _run():
        client = ViceClient(args.host, args.port)
        if args.action == "run":
            prg = _read_bytes(args.file)
            result = await client.run_async(args.emulator, prg, args.name or "PROGRAM", True)
            print(f"[OK] {args.file} running in VICE")
        elif args.action == "load":
            prg = _read_bytes(args.file)
            result = await client.transfer_async(args.emulator, prg, args.name or "PROGRAM", True)
            print(f"[OK] {args.file} loaded in VICE (not running)")
        elif args.action == "reset":
            await client.reset_async(args.emulator)
            print("[OK] VICE reset")
        elif args.action == "reboot":
            await client.reboot_async(args.emulator)
            print("[OK] VICE reboot")

    asyncio.run(_run())


# ── argument parser ───────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readycode",
        description="READYCode CLI — C64 BASIC tokenizer, disk image editor, and hardware bridges",
    )
    sub = parser.add_subparsers(dest="command")

    # tokenize
    p = sub.add_parser("tokenize", help="Tokenize BASIC source to .prg")
    p.add_argument("input", help="BASIC source file (.bas)")
    p.add_argument("-o", "--output", required=True, help="Output .prg file")
    p.set_defaults(func=cmd_tokenize)

    # detokenize
    p = sub.add_parser("detokenize", help="Detokenize .prg to BASIC source")
    p.add_argument("input", help="Tokenized .prg file")
    p.add_argument("-o", "--output", required=True, help="Output .bas file")
    p.set_defaults(func=cmd_detokenize)

    # disk — sub-subcommands via separate parsers
    p_disk = sub.add_parser("disk", help="Disk image operations")
    p_disk_sub = p_disk.add_subparsers(dest="disk_action")

    # disk list
    p = p_disk_sub.add_parser("list", help="List directory of a disk image")
    p.add_argument("image", help="Disk image file (.d64/.d81)")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.set_defaults(func=cmd_disk_list)

    # disk extract
    p = p_disk_sub.add_parser("extract", help="Extract a file from a disk image")
    p.add_argument("image", help="Disk image file (.d64/.d81)")
    p.add_argument("name", help="File name on disk")
    p.add_argument("-o", "--output", help="Output file (default: NAME.prg)")
    p.set_defaults(func=cmd_disk_extract)

    # disk inject
    p = p_disk_sub.add_parser("inject", help="Inject a file into a disk image")
    p.add_argument("image", help="Disk image file (.d64/.d81)")
    p.add_argument("file", help="Local file to inject")
    p.add_argument("--name", help="Name on disk (default: filename stem)")
    p.set_defaults(func=cmd_disk_inject)

    # disk create
    p = p_disk_sub.add_parser("create", help="Create a blank disk image")
    p.add_argument("-o", "--output", required=True, help="Output image file")
    p.add_argument("--name", help="Disk label (default: UNTITLED)")
    p.add_argument("--format", choices=["d64", "d81"], default="d64", help="Disk format (default: d64)")
    p.set_defaults(func=cmd_disk_create)

    # disk delete
    p = p_disk_sub.add_parser("delete", help="Delete a file from a disk image")
    p.add_argument("image", help="Disk image file (.d64/.d81)")
    p.add_argument("name", help="File name on disk")
    p.set_defaults(func=cmd_disk_delete)

    # disk rename
    p = p_disk_sub.add_parser("rename", help="Rename a file on a disk image")
    p.add_argument("image", help="Disk image file (.d64/.d81)")
    p.add_argument("name", help="Current file name on disk")
    p.add_argument("new_name", help="New file name")
    p.set_defaults(func=cmd_disk_rename)

    # minify
    p = sub.add_parser("minify", help="Minify BASIC source (reduce size)")
    p.add_argument("input", help="BASIC source file")
    p.add_argument("-o", "--output", required=True, help="Output file")
    p.add_argument("--keep-whitespace", action="store_true")
    p.add_argument("--keep-comments", action="store_true")
    p.add_argument("--keep-next-vars", action="store_true")
    p.add_argument("--keep-renumber", action="store_true")
    p.add_argument("--no-period", action="store_true")
    p.add_argument("--no-scientific", action="store_true")
    p.set_defaults(func=cmd_minify)

    # prettify
    p = sub.add_parser("prettify", help="Prettify BASIC source (improve readability)")
    p.add_argument("input", help="BASIC source file")
    p.add_argument("-o", "--output", required=True, help="Output file")
    p.add_argument("--no-whitespace", action="store_true")
    p.add_argument("--no-period", action="store_true")
    p.add_argument("--no-scientific", action="store_true")
    p.add_argument("--keep-next-vars", action="store_true")
    p.add_argument("--no-renumber", action="store_true")
    p.add_argument("--increment", type=int, default=10, help="Line number increment (default 10)")
    p.add_argument("--padding", type=int, default=0, help="Line number zero-padding width")
    p.set_defaults(func=cmd_prettify)

    # petscii
    p = sub.add_parser("petscii", help="Convert PETSCII to C64 screen code")
    p.add_argument("value", help="PETSCII value (decimal or $hex)")
    p.set_defaults(func=cmd_petscii)

    # bridge c64u
    p = sub.add_parser("bridge-c64u", help="C64 Ultimate bridge operations")
    p.add_argument("action", choices=["run", "list", "mount", "eject"])
    p.add_argument("--host", required=True, help="C64U IP address")
    p.add_argument("--file", help=".prg file to run")
    p.add_argument("--path", help="Remote path (for list/mount)")
    p.set_defaults(func=cmd_bridge_c64u)

    # bridge vice
    p = sub.add_parser("bridge-vice", help="VICE emulator bridge operations")
    p.add_argument("action", choices=["run", "load", "reset", "reboot"])
    p.add_argument("--host", default="127.0.0.1", help="VICE monitor host (default 127.0.0.1)")
    p.add_argument("--port", type=int, default=6510, help="VICE monitor port (default 6510)")
    p.add_argument("--emulator", default="x64sc", help="VICE emulator binary (default x64sc)")
    p.add_argument("--file", help=".prg file to run/load")
    p.add_argument("--name", help="Program name on C64")
    p.set_defaults(func=cmd_bridge_vice)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
