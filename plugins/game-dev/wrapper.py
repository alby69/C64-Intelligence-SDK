#!/usr/bin/env python3
"""Wrapper: game-dev plugin -> C64 GameDev kit (c64kit + c64lib, Space Invaders, template giochi)."""

import os
import sys
import subprocess
import shutil

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAMEDEV_DIR = os.path.join(SDK_ROOT, "gamedev")
GAMES_DIR = os.path.join(GAMEDEV_DIR, "games")


def _run(cmd, cwd=GAMEDEV_DIR, timeout=120):
    print(f"[C64] Esecuzione: {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    if r.stdout:
        print(f"[C64] {r.stdout[:4000]}")
    return r


def _list_games():
    if not os.path.isdir(GAMES_DIR):
        return []
    games = []
    for entry in sorted(os.listdir(GAMES_DIR)):
        full = os.path.join(GAMES_DIR, entry)
        if os.path.isdir(full):
            config = os.path.join(full, "c64project.yaml")
            games.append((entry, os.path.isfile(config)))
    return games


def cmd_list(args):
    print("[OK] C64 Game Development Kit")

    games = _list_games()
    if games:
        print("[OK] Giochi disponibili:")
        for name, has_config in games:
            tag = " (config build)" if has_config else ""
            print(f"[INFO]  games/{name}/{tag}")
    else:
        print("[C64] games/: nessun gioco trovato")

    for subdir, label in [
        ("c64kit", "Framework Python (emulazione HW, build pipeline, test)"),
        ("c64lib", "Libreria Assembly 6502 (HAL, sprite, collisioni, stati, HUD)"),
    ]:
        full = os.path.join(GAMEDEV_DIR, subdir)
        if os.path.isdir(full):
            n = len(os.listdir(full))
            print(f"[OK] {subdir}/: {label} ({n} elementi)")

    for mod in ["core", "video", "audio", "input", "game", "tools", "build", "testing"]:
        full = os.path.join(GAMEDEV_DIR, "c64kit", mod)
        if os.path.isdir(full):
            print(f"[OK]   c64kit/{mod}/")

    return 0


def cmd_build(args):
    config = "c64project.yaml"
    force = "--force" in args
    for i, a in enumerate(args):
        if a == "--config" and i + 1 < len(args):
            config = args[i + 1]

    if not os.path.isdir(GAMEDEV_DIR):
        print("[ERROR] Submodulo gamedev/ non inizializzato (git submodule update --init)")
        return 1
    if not os.path.isfile(os.path.join(GAMEDEV_DIR, config)):
        print(f"[ERROR] Config non trovata: {config} (usa --config per selezionare un gioco)")
        return 1

    cmd = [sys.executable, "-m", "c64kit.build.build_system", "--config", config]
    if force:
        cmd.append("--force")
    print(f"[OK] Build game (config: {config})")
    r = _run(cmd)
    if r.returncode != 0:
        print(f"[ERROR] Build fallita (exit {r.returncode})")
        if r.stderr:
            print(f"[ERROR] {r.stderr[:500]}")
        return 1
    print("[OK] Build completata")
    return 0


def cmd_new(args):
    if not args:
        print("[ERROR] Specifica il nome del gioco (es. MioGioco)")
        return 1
    name = args[0]

    script = os.path.join(GAMEDEV_DIR, "new_game.sh")
    if not os.path.isfile(script):
        print("[ERROR] new_game.sh non trovato nel submodulo gamedev/")
        return 1

    print(f"[OK] Bootstrap nuovo gioco: {name}")
    r = _run(["bash", script, name], timeout=60)
    if r.returncode != 0:
        print(f"[ERROR] Bootstrap fallito (exit {r.returncode})")
        if r.stderr:
            print(f"[ERROR] {r.stderr[:500]}")
        return 1
    print(f"[OK] Gioco creato: games/{name.lower()}/")
    return 0


def cmd_test(args):
    config = "c64project.yaml"
    for i, a in enumerate(args):
        if a == "--config" and i + 1 < len(args):
            config = args[i + 1]

    print("[OK] Test suite c64kit (pytest)")
    r = _run([sys.executable, "-m", "pytest", "-q", "tests"], timeout=180)
    if r.returncode != 0:
        print(f"[C64] pytest: exit {r.returncode}")
        # fallback: test headless VICE sulla config se presente
        if os.path.isfile(os.path.join(GAMEDEV_DIR, config)):
            print(f"[OK] Test headless VICE su {config}")
            r2 = _run([sys.executable, "-m", "c64kit.build.build_system", "--config", config], timeout=180)
            if r2.returncode != 0:
                print(f"[ERROR] Test fallito (exit {r2.returncode})")
                return 1
        else:
            print("[C64] Nessun test eseguito con successo")
            return 1
    print("[OK] Test completati")
    return 0


def cmd_run(args):
    target = args[0] if args else None
    disk = None
    for i, a in enumerate(args):
        if a == "--disk" and i + 1 < len(args):
            disk = args[i + 1]

    if disk and os.path.isfile(disk):
        cmd = ["x64sc", "-autostartprgmode", "0", "-autostartdiskimage", disk]
        print(f"[OK] Avvio VICE con disco {disk}")
    elif target:
        if not os.path.isabs(target):
            target = os.path.join(GAMEDEV_DIR, target)
        if not os.path.isfile(target):
            print(f"[ERROR] File PRG non trovato: {target}")
            return 1
        cmd = ["x64sc", target]
        print(f"[OK] Avvio VICE con {target}")
    else:
        print("[ERROR] Specifica un file .prg o --disk <file>.d64")
        return 1

    try:
        subprocess.Popen(cmd, cwd=GAMEDEV_DIR)
        print("[OK] Emulatore avviato")
    except FileNotFoundError:
        print("[ERROR] VICE (x64sc) non trovato. Installa VICE.")
        return 1
    return 0


def cmd_status(args):
    print("[OK] Stato C64 Game Development Kit")

    if not os.path.isdir(GAMEDEV_DIR):
        print("[ERROR] Submodulo gamedev/ non inizializzato (git submodule update --init)")
        return 1

    games = _list_games()
    print(f"[OK] Giochi: {len(games)}")
    for name, has_config in games:
        print(f"[INFO]  games/{name}/")

    for tool in ["xa", "c1541", "cartconv", "x64sc", "zip"]:
        found = shutil.which(tool)
        if found:
            print(f"[OK] {tool}: {found}")
        else:
            print(f"[C64] {tool}: non installato")

    return 0


def main():
    if len(sys.argv) < 2:
        print("[ERROR] Comando richiesto: list|build|new|test|run|status")
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "list": cmd_list,
        "build": cmd_build,
        "new": cmd_new,
        "test": cmd_test,
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
