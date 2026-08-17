# C64 Intelligence SDK

IDE moderna per lo sviluppo su Commodore 64. Compila, debugga, emula e sviluppa in BASIC V2 e Assembly 6502.

- [Architettura](../ARCHITECTURE.md) — principio "Standalone-first, Integrated-second", mappa moduli, definizione plugin
- [Quick Start](../README.md)
- [Compatibilità moduli](../README.md#compatibility-matrix)
- [Changelog](../CHANGELOG.md)
- [Contributing](../CONTRIBUTING.md)

## Moduli

| Mount point | Repository | Plugin |
|---|---|---|
| `core/` | C64-LLM | ai-agent |
| `tools/` | PYC64 | compiler, editor, project-manager |
| `tutorial/` | C64GameTutorial | tutorial |
| `scraper/` | C64-Scrapy | (alimenta kb-agent) |
| `kb-agent/` | C64-KB-Agent | knowledge |
| `debugger/` | C64-Debugger | debugger |
| `editor/` | C64-Code | disk-tools, emulator |
| `geckos/` | C64-OS | geckos |
| `submodules/c64-gamedev/` | C64-GameDev | game-dev |

Ogni modulo resta autonomo: documentazione e sorgenti vivono nei rispettivi sub-repo e sono aggregati qui per riferimento (vedi `scripts/sync_docs.py`).