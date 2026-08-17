#!/usr/bin/env python3
"""Sincronizza i docs dei submodule in site-docs/ per il sito MkDocs unificato.

Usa symlink (riferimenti), non copie manuali: i contenuti restano nei singoli
sub-repo (disaccoppiamento). Eseguire: python3 scripts/sync_docs.py
"""

import os
import sys

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGING = os.path.join(SDK_ROOT, "site-docs", "modules")

MODULES = {
    "core": "C64-LLM",
    "tools": "PYC64",
    "tutorial": "C64GameTutorial",
    "scraper": "C64-Scrapy",
    "kb-agent": "C64-KB-Agent",
    "debugger": "C64-Debugger",
    "editor": "C64-Code",
    "geckos": "C64-OS",
    "gamedev": "C64-GameDev",
}


def sync():
    os.makedirs(STAGING, exist_ok=True)
    for name, label in MODULES.items():
        src = os.path.join(SDK_ROOT, name, "docs")
        dst = os.path.join(STAGING, name)
        if os.path.islink(dst) or os.path.isdir(dst):
            os.unlink(dst)
        if os.path.isdir(src):
            os.symlink(src, dst)
            print(f"linked: {name}/docs -> site-docs/modules/{name}")
        else:
            print(f"skip (nessun docs/): {name}")


if __name__ == "__main__":
    sys.exit(sync())