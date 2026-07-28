#!/usr/bin/env python3
"""Wrapper: tutorial plugin -> C64 Game Tutorial (27 capitoli, soluzioni, template)."""

import os
import sys
import glob as pyglob

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TUTORIAL_DIR = os.path.join(SDK_ROOT, "tutorial")

PARTS = {
    1: (1, 3, "Fondamenti di 6502 e Turbo Macro Pro"),
    2: (4, 6, "Grafica e sprite (VIC-II)"),
    3: (7, 8, "Raster interrupt e sincronismo"),
    4: (9, 13, "Gameplay (joystick, collisioni, pool, wave, stati)"),
    5: (14, 15, "Audio SID"),
    6: (16, 18, "Tecniche avanzate (multiplex, parallax, boss)"),
    7: (19, 21, "Architettura professionale (kernel 3-layer, Arcade OS, custom loader)"),
    8: (22, 24, "Strumenti e rifiniture (debugging VICE, titolo/high score, scrolling)"),
    9: (25, 27, "Hardware avanzato (turbo loader, REU, music tracker)"),
}

# File naming in tutorial/md/: "XX-titolo.md" (IT) / tutorial/en/: "XX-title.md" (EN)
CHAPTER_FILES_IT = [
    "01-introduzione-c64-tmp", "02-istruzioni-fondamentali",
    "03-indirizzamento-cicli-ritardi", "04-memoria-video-e-caratteri",
    "05-sprite-hardware-vic-ii", "06-movimento-e-controllo-sprite",
    "07-raster-interrupt", "08-game-loop-sincronizzato",
    "09-joystick-e-input", "10-collisioni-software",
    "11-sistema-proiettili", "12-wave-system-e-ai-nemici",
    "13-punteggio-e-stati-gioco", "14-audio-sid-base",
    "15-audio-engine-e-sfx", "16-multiplex-degli-sprite",
    "17-effetto-parallasse", "18-boss-fight",
    "19-architettura-3-layer", "20-arcade-os",
    "21-custom-loader", "22-debugging-con-vice",
    "23-titolo-e-highscore", "24-scrolling-avanzato",
    "25-turbo-loader", "26-ram-expansion-unit-reu",
    "27-music-tracker",
]
CHAPTER_FILES_EN = [
    "01-introduction-c64-tmp", "02-fundamental-instructions",
    "03-addressing-loops-delays", "04-video-memory-and-characters",
    "05-sprite-hardware-vic-ii", "06-sprite-movement-and-control",
    "07-raster-interrupt", "08-synchronized-game-loop",
    "09-joystick-and-input", "10-software-collisions",
    "11-projectile-system", "12-wave-system-and-ai-enemies",
    "13-score-and-game-states", "14-audio-sid-basics",
    "15-audio-engine-and-sfx", "16-sprite-multiplex",
    "17-parallax-effect", "18-boss-fight",
    "19-three-layer-architecture", "20-arcade-os",
    "21-custom-loader", "22-debugging-with-vice",
    "23-title-and-highscore", "24-advanced-scrolling",
    "25-turbo-loader", "26-reu-ram-expansion-unit",
    "27-music-tracker",
]

CHAPTER_NAMES = {
    "cap01": "Introduzione a C64 e TMP",
    "cap02": "Primi passi in Assembly 6502",
    "cap03": "Strutture di controllo e subroutine",
    "cap04": "Modalità grafiche del VIC-II",
    "cap05": "Sprite: definizione e movimento",
    "cap06": "Gestione delle collisioni",
    "cap07": "Raster interrupt: teoria",
    "cap08": "Raster interrupt: applicazioni pratiche",
    "cap09": "Il joystick: lettura input",
    "cap10": "Pool di sprite e gestione oggetti",
    "cap11": "Sistema a onde (wave system)",
    "cap12": "Macchina a stati per il gameplay",
    "cap13": "Collisioni avanzate",
    "cap14": "Il SID: teoria audio",
    "cap15": "Il SID: musica ed effetti",
    "cap16": "Multiplex degli sprite",
    "cap17": "Effetti parallasse",
    "cap18": "Boss fight",
    "cap19": "Architettura 3-layer",
    "cap20": "Arcade OS",
    "cap21": "Custom loader",
    "cap22": "Debugging con VICE",
    "cap23": "Titolo e high score",
    "cap24": "Scrolling avanzato",
    "cap25": "Turbo loader",
    "cap26": "REU (RAM Expansion Unit)",
    "cap27": "Music tracker",
}


def get_chapter_part(chapter_num):
    for part, (start, end, _) in PARTS.items():
        if start <= chapter_num <= end:
            return part
    return 0


def cmd_list(args):
    part_filter = None
    for i, a in enumerate(args):
        if a == "--part" and i + 1 < len(args):
            part_filter = int(args[i + 1])

    print("[OK] C64 Game Tutorial — 27 capitoli")

    for part, (start, end, title) in sorted(PARTS.items()):
        if part_filter and part != part_filter:
            continue
        print(f"\n[ASM] Parte {part}: {title} (cap{start:02d}-cap{end:02d})")
        for ch in range(start, end + 1):
            idx = ch - 1
            name = CHAPTER_NAMES.get(f"cap{ch:02d}", f"Capitolo {ch}")

            it_file = None
            if idx < len(CHAPTER_FILES_IT):
                it_file = os.path.join(TUTORIAL_DIR, "md", f"{CHAPTER_FILES_IT[idx]}.md")
            en_file = None
            if idx < len(CHAPTER_FILES_EN):
                en_file = os.path.join(TUTORIAL_DIR, "en", f"{CHAPTER_FILES_EN[idx]}.md")

            found = None
            lang_tag = ""
            if it_file and os.path.isfile(it_file):
                found = it_file
                lang_tag = ""
            elif en_file and os.path.isfile(en_file):
                found = en_file
                lang_tag = " (EN)"

            if found:
                sz = os.path.getsize(found)
                sz_str = f"{sz}B" if sz < 1024 else f"{sz // 1024}KB"
                print(f"[INFO]   Cap {ch:02d}: {name:45s} {sz_str:>8s}{lang_tag}")
            else:
                print(f"[C64]   Cap {ch:02d}: {name} (file non trovato)")

    # Reference tables
    print("\n[C64] Appendici: A (Tabelle), B (Glossario), C-F (Schemi rapidi), G (Risorse), TMP (Guida TMP)")
    print(f"[BASIC] Soluzioni: in tutorial/soluzioni/")
    print(f"[BASIC] Template gioco: in tutorial/game/")

    return 0


def cmd_show(args):
    if not args:
        print("[ERROR] Specifica un capitolo (es. cap01, 1, o '01-introduzione')")
        return 1

    chapter = args[0]
    lang = "it"
    for i, a in enumerate(args):
        if a == "--lang" and i + 1 < len(args):
            lang = args[i + 1]

    # Normalize: "1" -> "01" (two digits)
    if chapter.isdigit():
        chapter = f"{int(chapter):02d}"

    # Strip "cap" prefix if present
    chapter_clean = chapter.replace("cap", "")

    chapter_list = CHAPTER_FILES_EN if lang == "en" else CHAPTER_FILES_IT

    # Find by number or by partial name
    filepath = None
    if chapter_clean.isdigit():
        idx = int(chapter_clean) - 1
        if 0 <= idx < len(chapter_list):
            lang_dir = "en" if lang == "en" else "md"
            candidate = os.path.join(TUTORIAL_DIR, lang_dir, f"{chapter_list[idx]}.md")
            if os.path.isfile(candidate):
                filepath = candidate
    else:
        # Try to match partial name
        lang_dir = "en" if lang == "en" else "md"
        full_dir = os.path.join(TUTORIAL_DIR, lang_dir)
        if os.path.isdir(full_dir):
            for f in os.listdir(full_dir):
                if f.endswith(".md") and (chapter.lower() in f.lower() or chapter_clean in f):
                    filepath = os.path.join(full_dir, f)
                    break

    if not filepath:
        # Try soluzioni
        sol_path = os.path.join(TUTORIAL_DIR, "soluzioni", f"{chapter}.asm")
        if os.path.isfile(sol_path):
            filepath = sol_path

    if not filepath:
        print(f"[ERROR] Capitolo '{chapter}' non trovato ({lang})")
        print(f"[C64] Usa 'list' per vedere i capitoli disponibili")
        return 1
    with open(filepath, errors="replace") as f:
        content = f.read()

    lines = content.split("\n")
    title = lines[0].strip("# ") if lines else os.path.basename(filepath)
    print(f"[OK] {title}")
    print(f"[PRG] {filepath} ({len(content)} byte, {len(lines)} righe)")
    print()

    # Show first 40 lines
    for line in lines[:40]:
        if line.strip():
            stripped = line.strip()
            if stripped.startswith("# "):
                print(f"[OK] {stripped}")
            elif stripped.startswith("##"):
                print(f"[INFO] {stripped}")
            elif stripped.startswith("- "):
                print(f"[C64] {stripped}")
            else:
                print(f"[C64] {stripped}")
    if len(lines) > 40:
        print(f"\n[C64] ... ({len(lines) - 40} righe in più)")

    return 0


def cmd_example(args):
    if not args:
        print("[ERROR] Specifica un nome di soluzione (es. cap01 o cap01-introduzione)")
        return 1

    name = args[0]
    chapter_filter = None
    for i, a in enumerate(args):
        if a == "--chapter" and i + 1 < len(args):
            chapter_filter = args[i + 1]

    sol_dir = os.path.join(TUTORIAL_DIR, "soluzioni")
    if not os.path.isdir(sol_dir):
        print("[ERROR] Directory soluzioni non trovata")
        return 1

    matches = []
    if chapter_filter:
        pattern = os.path.join(sol_dir, f"{chapter_filter}-*.asm")
        matches = pyglob.glob(pattern)
    else:
        pattern = os.path.join(sol_dir, f"*{name}*.asm")
        matches = pyglob.glob(pattern)

    if not matches:
        pattern = os.path.join(sol_dir, f"{name}")
        if os.path.isfile(pattern):
            matches = [pattern]

    if not matches:
        # List all available
        all_sol = sorted(pyglob.glob(os.path.join(sol_dir, "*.asm")))
        print(f"[ERROR] Soluzione '{name}' non trovata. Disponibili:")
        for s in all_sol[:10]:
            print(f"[INFO]  {os.path.basename(s)}")
        return 1

    filepath = matches[0]
    with open(filepath) as f:
        content = f.read()

    lines = content.split("\n")
    print(f"[OK] Soluzione: {os.path.basename(filepath)}")
    print(f"[PRG] {filepath} ({len(content)} byte, {len(lines)} righe)")
    print()
    for line in lines[:50]:
        if line.strip():
            print(f"[ASM] {line}")
    if len(lines) > 50:
        print(f"[C64] ... ({len(lines) - 50} righe in più)")

    return 0


def cmd_template(args):
    output_dir = args[0] if args else None
    if not output_dir:
        print("[ERROR] Specifica una directory di output")
        return 1

    game_dir = os.path.join(TUTORIAL_DIR, "game")
    if not os.path.isdir(game_dir):
        print("[ERROR] Template gioco non trovato in tutorial/game/")
        return 1

    import shutil
    os.makedirs(output_dir, exist_ok=True)
    for item in os.listdir(game_dir):
        src = os.path.join(game_dir, item)
        dst = os.path.join(output_dir, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    print(f"[OK] Template gioco copiato in {output_dir}")
    files = os.listdir(output_dir)
    print(f"[OK] {len(files)} file copiati:")
    for f in sorted(files):
        fp = os.path.join(output_dir, f)
        sz = os.path.getsize(fp)
        if os.path.isfile(fp):
            print(f"[INFO]  {f:40s} {sz}B")
        else:
            print(f"[BASIC] {f:40s} (directory)")

    return 0


def cmd_search(args):
    if not args:
        print("[ERROR] Specifica una query di ricerca")
        return 1
    query = " ".join(args).lower()

    results = []
    for lang_dir in ["md", "en"]:
        full = os.path.join(TUTORIAL_DIR, lang_dir)
        if not os.path.isdir(full):
            continue
        for f in sorted(os.listdir(full)):
            if f.endswith(".md"):
                fp = os.path.join(full, f)
                with open(fp, errors="replace") as fh:
                    content = fh.read()
                if query in content.lower():
                    lines = content.split("\n")
                    title = lines[0].strip("# ")
                    # Find matching lines
                    matching = [l.strip() for l in lines if query in l.lower()]
                    results.append((fp, title, len(content), matching[:3]))

    # Also search soluzioni
    sol_dir = os.path.join(TUTORIAL_DIR, "soluzioni")
    if os.path.isdir(sol_dir):
        for f in sorted(os.listdir(sol_dir)):
            if f.endswith(".asm"):
                fp = os.path.join(sol_dir, f)
                with open(fp, errors="replace") as fh:
                    content = fh.read()
                if query in content.lower():
                    matching = [l.strip() for l in content.split("\n") if query in l.lower()]
                    results.append((fp, f, len(content), matching[:3]))

    if results:
        print(f"[OK] Trovati {len(results)} risultati per '{query}':")
        for fp, title, sz, matches in results:
            rel = os.path.relpath(fp, TUTORIAL_DIR)
            print(f"\n[INFO] {rel} ({sz // 1024}KB)")
            for m in matches[:2]:
                print(f"[C64]   ...{m[:80]}...")
    else:
        print(f"[C64] Nessun risultato per '{query}'")

    return 0


def cmd_references(args):
    appendix = None
    for i, a in enumerate(args):
        if a == "--appendix" and i + 1 < len(args):
            appendix = args[i + 1].upper()

    appendices = {
        "A": "Tabelle (colori, registri VIC-II/SID/CIA, istruzioni 6502)",
        "B": "Glossario",
        "C": "Schemi rapidi: CPU e memoria",
        "D": "Schemi rapidi: video e sprite",
        "E": "Schemi rapidi: architettura di gioco",
        "F": "Schemi rapidi: audio e hardware",
        "G": "Risorse esterne: libri, siti e tutorial",
        "TMP": "Guida rapida a Turbo Macro Pro",
    }

    if appendix:
        if appendix not in appendices:
            print(f"[ERROR] Appendice '{appendix}' non trovata. Disponibili: {', '.join(appendices.keys())}")
            return 1
        print(f"[OK] Appendice {appendix}: {appendices[appendix]}")
        # Try to find the appendix file
        pattern = os.path.join(TUTORIAL_DIR, "md", f"appendix-{appendix.lower()}.md")
        if not os.path.isfile(pattern):
            pattern = os.path.join(TUTORIAL_DIR, "md", f"appendice-{appendix.lower()}.md")
        if os.path.isfile(pattern):
            with open(pattern) as f:
                content = f.read()
            lines = content.split("\n")
            for line in lines[:30]:
                if line.strip():
                    print(f"[C64] {line.strip()}")
            if len(lines) > 30:
                print(f"[C64] ... ({len(lines) - 30} righe in più)")
        else:
            print(f"[C64] File appendice non trovato: {pattern}")
    else:
        print("[OK] Appendici del manuale C64 Game Tutorial:")
        for letter, desc in sorted(appendices.items()):
            print(f"[INFO]  {letter}: {desc}")

    return 0


def main():
    if len(sys.argv) < 2:
        print("[ERROR] Comando richiesto: list|show|example|template|search|references")
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "list": cmd_list,
        "show": cmd_show,
        "example": cmd_example,
        "template": cmd_template,
        "search": cmd_search,
        "references": cmd_references,
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
