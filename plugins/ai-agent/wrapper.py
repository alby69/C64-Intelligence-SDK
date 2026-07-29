#!/usr/bin/env python3
"""Wrapper: ai-agent plugin -> core/ C64 Coding Agent."""

import os
import sys
import json
import shutil

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SDK_ROOT, "core"))


def cmd_generate(args):
    prompt = " ".join(args) if args else "genera codice C64"
    try:
        from agent.agent_pro import C64CodingAgent, get_hints
    except ImportError:
        print(
            "[ERROR] core/agent modules not available. Run `pip install -r core/requirements.txt`"
        )
        return 1

    print(f"[OK] Generazione codice da prompt: {prompt}")
    hints = get_hints(prompt)
    if hints:
        print(f"[INFO] Suggerimenti:\n{hints}")

    agent = C64CodingAgent(gguf_path=os.environ.get("GGUF_PATH"))
    response, sources, logs = agent.orchestrator.process_request(
        prompt, use_rag=True, max_attempts=3
    )
    print(f"[OK] Codice generato ({len(response)} caratteri)")
    print(response)

    output = None
    for i, a in enumerate(args):
        if a in ("-o", "--output") and i + 1 < len(args):
            output = args[i + 1]
    if output:
        with open(output, "w") as f:
            f.write(response)
        print(f"[OK] Salvato: {output}")
    return 0


def cmd_explain(args):
    input_path = args[0] if args else None
    if input_path and os.path.isfile(input_path):
        with open(input_path) as f:
            code = f.read()
        print(f"[OK] Analisi di {input_path} ({len(code)} byte)")
    else:
        code = input_path or ""
        print("[OK] Analisi codice fornito come argomento")

    detail = "full"
    for i, a in enumerate(args):
        if a == "--detail" and i + 1 < len(args):
            detail = args[i + 1]

    try:
        from agent.agent_pro import C64CodingAgent

        agent = C64CodingAgent(gguf_path=os.environ.get("GGUF_PATH"))
        prompt = f"Spiega questo codice C64 in modo {'dettagliato' if detail == 'full' else 'breve'}:\n{code}"
        response, sources, logs = agent.orchestrator.process_request(
            prompt, use_rag=True
        )
        print(f"[OK] Spiegazione completata")
        print(response)
    except ImportError:
        print("[INFO] AI agent non disponibile, mostro analisi base")
        print(f"File: {input_path or '(inline)'}")
        print(f"Lunghezza: {len(code)} byte")
        lines = code.split("\n")
        print(f"Righe: {len(lines)}")
    return 0


def cmd_optimize(args):
    input_path = args[0] if args else None
    if not input_path or not os.path.isfile(input_path):
        print("[ERROR] Specifica un file .c64 o .asm da ottimizzare")
        return 1
    with open(input_path) as f:
        code = f.read()
    print(f"[OK] Ottimizzazione di {input_path}")
    try:
        from agent.agent_pro import C64CodingAgent

        agent = C64CodingAgent(gguf_path=os.environ.get("GGUF_PATH"))
        prompt = f"Ottimizza questo codice C64 per velocità e dimensione:\n{code}"
        response, sources, logs = agent.orchestrator.process_request(
            prompt, use_rag=True
        )
        print(response)
    except ImportError:
        print("[INFO] AI agent non disponibile")
        print("[INFO] Ottimizzazioni standard suggerite:")
        if "poke(" in code.lower():
            print("  - Raggruppa POKE consecutivi")
        if "for" in code.lower():
            print("  - Usa variabili locali nei loop")
    return 0


def cmd_debug(args):
    input_path = args[0] if args else None
    if not input_path or not os.path.isfile(input_path):
        print("[ERROR] Specifica un file sorgente o crash dump")
        return 1
    with open(input_path) as f:
        content = f.read()

    crash_path = None
    for i, a in enumerate(args):
        if a == "--crash" and i + 1 < len(args):
            crash_path = args[i + 1]

    crash_dump = ""
    if crash_path and os.path.isfile(crash_path):
        with open(crash_path) as f:
            crash_dump = f.read()

    print(f"[OK] Analisi debug di {input_path}")
    try:
        from agent.agent_pro import C64CodingAgent

        agent = C64CodingAgent(gguf_path=os.environ.get("GGUF_PATH"))
        prompt = f"Analizza e correggi errori in questo codice C64:\n{content}"
        if crash_dump:
            prompt += f"\nCrash dump:\n{crash_dump}"
        response, sources, logs = agent.orchestrator.process_request(
            prompt, use_rag=True
        )
        print(response)
    except ImportError:
        print("[INFO] AI agent non disponibile per analisi avanzata")
        print("[SIZE]", len(content), "byte")
    return 0


def cmd_status(args):
    print("[OK] Stato C64 AI Coding Agent")
    core_path = os.path.join(SDK_ROOT, "core")
    for path, label in [
        ("knowledge_base", "File Markdown KB"),
        ("data/input", "File input"),
        ("data/vectorstore", "Indice vettoriale"),
    ]:
        full = os.path.join(core_path, path)
        if os.path.isdir(full):
            try:
                files = [f for f in os.listdir(full) if not f.startswith(".")]
                print(f"[OK] {label}: {len(files)}")
            except OSError as e:
                print(f"[C64] {label}: errore lettura ({e})")
        else:
            print(f"[C64] {label}: assente")
    ds = os.path.join(core_path, "data/output/dataset_unified.jsonl")
    if os.path.exists(ds):
        with open(ds) as f:
            n = sum(1 for _ in f)
        print(f"[OK] Dataset entries: {n}")
    return 0


def cmd_search(args):
    query = " ".join(args) if args else ""
    if not query:
        print("[ERROR] Specifica una query di ricerca")
        return 1
    try:
        from agent.knowledge_base import C64KnowledgeBase

        kb = C64KnowledgeBase()
        results = kb.search(query)
        print(f"[OK] Ricerca KB: '{query}'")
        if results:
            for r in results[:10]:
                print(f"[INFO] {r}")
        else:
            print("[C64] Nessun risultato trovato")
    except ImportError:
        print("[ERROR] Knowledge Base non disponibile")
    return 0


def cmd_distill(args):
    print(
        f"[OK] Avvio distillazione (usa core/config/teacher_config.yaml per configurazione)"
    )
    try:
        from pipeline.knowledge_distiller import main as distill_main

        distill_main()
        print("[OK] Dataset distillato generato")
    except ImportError:
        print("[ERROR] Modulo distillazione non disponibile. Esegui da core/")
    return 0


def cmd_train(args):
    if len(args) < 2:
        print("[ERROR] Uso: train <dataset_path> <output_dir>")
        return 1
    dataset_path, output_dir = args[0], args[1]
    print(f"[OK] Avvio training LoRA da {dataset_path} -> {output_dir}")
    try:
        from pipeline.train_lora import train

        train(dataset_path, output_dir)
        print(f"[OK] Modello salvato in {output_dir}")
    except ImportError:
        print("[ERROR] Modulo training non disponibile")
    return 0


def main():
    if len(sys.argv) < 2:
        print(
            "[ERROR] Comando richiesto: generate|explain|optimize|debug|status|search|distill|train"
        )
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "generate": cmd_generate,
        "explain": cmd_explain,
        "optimize": cmd_optimize,
        "debug": cmd_debug,
        "status": cmd_status,
        "search": cmd_search,
        "distill": cmd_distill,
        "train": cmd_train,
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
