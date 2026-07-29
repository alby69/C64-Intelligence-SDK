#!/usr/bin/env python3
"""Wrapper: knowledge plugin -> kb-agent (Knowledge Base with FAISS + SQLite FTS5)."""

import os
import sys
import json

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB_AGENT_DIR = os.path.join(SDK_ROOT, "kb-agent")
CORE_DIR = os.path.join(SDK_ROOT, "core")
sys.path.insert(0, KB_AGENT_DIR)
sys.path.insert(0, CORE_DIR)


def _resolve_kb_dir():
    """Resolve knowledge_base directory, handling git symlinks on Windows."""
    kb_dir = os.path.join(CORE_DIR, "knowledge_base")
    if os.path.isdir(kb_dir):
        return kb_dir
    if os.path.isfile(kb_dir):
        with open(kb_dir) as f:
            target = f.read().strip()
        resolved = os.path.join(SDK_ROOT, target.replace("/", os.sep))
        if os.path.isdir(resolved):
            return resolved
    fallback = os.path.join(KB_AGENT_DIR, "data", "docs")
    if os.path.isdir(fallback):
        return fallback
    return None


def cmd_search(args):
    if not args:
        print("[ERROR] Specifica una query di ricerca")
        return 1
    query = " ".join(args)
    max_results = 10
    for i, a in enumerate(args):
        if a == "--max-results" and i + 1 < len(args):
            max_results = int(args[i + 1])

    # Try kb-agent FAISS search first
    kb_search_path = os.path.join(KB_AGENT_DIR, "data", "dataset")
    docs_path = os.path.join(KB_AGENT_DIR, "data", "docs")

    results = []
    # Search in docs recursively
    if os.path.isdir(docs_path):
        ql = query.lower()
        for root, _, files in os.walk(docs_path):
            for f in files:
                if f.endswith(".md"):
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, "r", errors="replace") as fh:
                            content = fh.read()
                        if ql in content.lower():
                            lines = content.split("\n")
                            title = lines[0].strip("# ")
                            results.append((fp, title, len(content)))
                    except:
                        pass
        results.sort(key=lambda x: -x[2])
        results = results[:max_results]

    if results:
        print(f"[OK] Trovati {len(results)} risultati per '{query}':")
        for fp, title, sz in results:
            rel = os.path.relpath(fp, docs_path)
            sz_str = f"{sz}B" if sz < 1024 else f"{sz // 1024}KB"
            print(f"[BASIC] {rel:60s} {sz_str:>8s}")
            print(f"[INFO]  {title}")
    else:
        # Fallback: search in resolved knowledge_base
        kb_dir = _resolve_kb_dir()
        if kb_dir:
            ql = query.lower()
            for root, _, files in os.walk(kb_dir):
                for f in files:
                    if f.endswith(".md"):
                        fp = os.path.join(root, f)
                        try:
                            with open(fp, "r") as fh:
                                content = fh.read()
                            if ql in content.lower():
                                title = content.split("\n")[0].strip("# ")
                                results.append((fp, title, len(content)))
                        except:
                            pass
            results.sort(key=lambda x: -x[2])
            results = results[:max_results]

        if results:
            rel = os.path.relpath
            print(
                f"[OK] Trovati {len(results)} risultati in Knowledge Base per '{query}':"
            )
            for fp, title, sz in results:
                r = os.path.relpath(fp, kb_dir)
                print(f"[INFO] {r}")
                print(f"[INFO]   {title}")
        else:
            print(f"[C64] Nessun risultato per '{query}'")

    return 0


def cmd_docs(args):
    if not args:
        print("[ERROR] Specifica un topic (es. sprite, raster, sid)")
        return 1
    topic = " ".join(args)

    source = "all"
    for i, a in enumerate(args):
        if a == "--source" and i + 1 < len(args):
            source = args[i + 1]

    kb_dir = _resolve_kb_dir()
    if not kb_dir:
        print(f"[ERROR] Knowledge base non trovata")
        return 1

    kb_topics = {
        "sprite": "sprite_programming.md",
        "raster": "raster_interrupts.md",
        "raster interrupt": "raster_interrupts.md",
        "sid": "sid_programming.md",
        "sound": "sid_programming.md",
        "memory": "c64_memory_map.md",
        "kernal": "kernal_routines.md",
        "vic": "vic2_registers.md",
        "vic-ii": "vic2_registers.md",
        "addressing": "6502_addressing_modes.md",
        "cia": "c64_cia_chips.md",
        "screen": "c64_screen_routines.md",
        "basic": "c64_basic_tutorial.md",
    }

    found = False
    tl = topic.lower()
    for key, filename in kb_topics.items():
        if key in tl:
            fp = os.path.join(kb_dir, filename)
            if os.path.isfile(fp):
                with open(fp) as f:
                    content = f.read()
                lines = content.split("\n")
                title = lines[0].strip("# ") if lines else filename
                print(f"[OK] Documentazione: {title}")
                for line in lines[:30]:
                    if line.strip():
                        print(f"[C64] {line.strip()}")
                if len(lines) > 30:
                    print(
                        f"[INFO] ... ({len(lines) - 30} righe in più. File: {filename})"
                    )
                found = True
                break

    if not found:
        print(f"[C64] Nessuna documentazione specifica per '{topic}'")
        print(f"[C64] Topics disponibili: {', '.join(kb_topics.keys())}")

    return 0


def cmd_status(args):
    print("[OK] Stato Knowledge Base")

    for label, path in [
        ("kb-agent docs", os.path.join(KB_AGENT_DIR, "data", "docs")),
        ("kb-agent dataset", os.path.join(KB_AGENT_DIR, "data", "dataset")),
        (
            "core knowledge_base",
            _resolve_kb_dir() or os.path.join(CORE_DIR, "knowledge_base"),
        ),
    ]:
        if os.path.isdir(path):
            files = []
            for root, _, fnames in os.walk(path):
                for f in fnames:
                    fp = os.path.join(root, f)
                    files.append(fp)
            total_sz = sum(os.path.getsize(f) for f in files if os.path.isfile(f))
            sz_str = f"{total_sz // 1024}KB" if total_sz > 1024 else f"{total_sz}B"
            print(f"[OK] {label}: {len(files)} file ({sz_str})")
        else:
            print(f"[C64] {label}: assente")

    # Check search index
    for idx_name, idx_path in [
        ("FAISS index", "data/vectorstore"),
        ("SQLite FTS5", "data/dataset/search_index.db"),
    ]:
        full = os.path.join(KB_AGENT_DIR, idx_path)
        if os.path.exists(full):
            print(f"[OK] {idx_name}: presente")
        else:
            full2 = os.path.join(CORE_DIR, idx_path)
            if os.path.exists(full2):
                print(f"[OK] {idx_name}: presente (in core/)")
            else:
                print(f"[C64] {idx_name}: assente")

    return 0


def cmd_list_api(args):
    filter_term = None
    for i, a in enumerate(args):
        if a == "--filter" and i + 1 < len(args):
            filter_term = args[i + 1]

    # Look for API index
    api_idx = os.path.join(KB_AGENT_DIR, "data", "dataset", "api_index.json")
    if not os.path.isfile(api_idx):
        api_idx = os.path.join(KB_AGENT_DIR, "data", "api_index.json")
    if not os.path.isfile(api_idx):
        print("[OK] Indice API C64")
        kb_dir = _resolve_kb_dir()
        kb_topics = {
            "KERNAL": "kernal_routines.md",
            "VIC-II": "vic2_registers.md",
            "SID": "sid_programming.md",
            "CIA": "c64_cia_chips.md",
            "6502": "6502_addressing_modes.md",
            "SPRITE": "sprite_programming.md",
            "RASTER": "raster_interrupts.md",
            "MEMORY": "c64_memory_map.md",
            "SCREEN": "c64_screen_routines.md",
            "BASIC": "c64_basic_tutorial.md",
        }
        for name, fn in kb_topics.items():
            if filter_term and filter_term.lower() not in name.lower():
                continue
            if kb_dir:
                fp = os.path.join(kb_dir, fn)
                if os.path.isfile(fp):
                    sz = os.path.getsize(fp)
                    print(f"[OK] {name:12s} -> {fn} ({sz // 1024}KB)")
        return 0

    with open(api_idx, "r", encoding="utf-8", errors="replace") as f:
        apis = json.load(f)

    print(f"[OK] Indice API C64 ({len(apis)} entry)")
    for api in apis:
        name = api.get("name", "")
        desc = api.get("description", "")
        if filter_term and filter_term.lower() not in name.lower():
            continue
        if desc:
            print(f"[OK] {name:30s}  {desc[:60]}")
        else:
            print(f"[OK] {name}")

    return 0


def cmd_list_files(args):
    target_dir = "docs"
    for i, a in enumerate(args):
        if a == "--dir" and i + 1 < len(args):
            target_dir = args[i + 1]

    if target_dir == "docs":
        paths = [
            ("kb-agent docs", os.path.join(KB_AGENT_DIR, "data", "docs")),
            (
                "core knowledge_base",
                _resolve_kb_dir() or os.path.join(CORE_DIR, "knowledge_base"),
            ),
        ]
    else:
        paths = [
            ("kb-agent dataset", os.path.join(KB_AGENT_DIR, "data", "dataset")),
            ("core dataset", os.path.join(CORE_DIR, "data", "output")),
        ]

    for label, path in paths:
        if not os.path.isdir(path):
            print(f"[C64] {label}: {path} non trovato")
            continue
        files = []
        for root, _, fnames in os.walk(path):
            for f in fnames:
                fp = os.path.join(root, f)
                sz = os.path.getsize(fp)
                rel = os.path.relpath(fp, path)
                files.append((rel, sz))
        files.sort(key=lambda x: -x[1])
        print(f"[OK] {label} ({len(files)} file):")
        for rel, sz in files[:20]:
            sz_str = f"{sz}B" if sz < 1024 else f"{sz // 1024}KB"
            print(f"[INFO]  {rel:60s} {sz_str:>8s}")
        if len(files) > 20:
            print(f"[C64]  ... e altri {len(files) - 20} file")

    return 0


def main():
    if len(sys.argv) < 2:
        print("[ERROR] Comando richiesto: search|docs|status|list-api|list-files")
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "search": cmd_search,
        "docs": cmd_docs,
        "status": cmd_status,
        "list-api": cmd_list_api,
        "list-files": cmd_list_files,
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
