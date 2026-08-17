# Architettura — C64 Intelligence SDK

> Versione: 1.0 · Data: 2026-08-17 · Stato: adottata (ADR-0001)

## Principio guida: "Standalone-first, Integrated-second"

Ogni sub-repo può essere **clonato da solo, installato da solo, testato da solo e usato da solo**, senza mai richiedere la presenza del repo wrapper.

Il repo wrapper `C64-Intelligence-SDK` **non contiene logica di dominio**: il suo unico compito è scoprire, validare le versioni, orchestrare ed esporre una CLI/UI unificata sopra componenti che restano autonomi.

Conseguenze operative:

- nessun import "hardcoded" di un submodule da parte di un altro: l'unico canale tra componenti è un **contratto dati versionato** (file, non codice);
- l'integrazione nell'SDK avviene **solo tramite manifest dichiarativo** (vedi §4);
- una modifica a un submodule non deve mai rompere un altro submodule, né l'SDK, senza che un test lo rilevi **prima del merge**.

## Mappa dei moduli

| Mount point | Repository | Ruolo | Branch | Packaging | Stato albero SDK |
|---|---|---|---|---|---|
| `core/` | [C64-LLM](https://github.com/alby69/C64-LLM) | Agenti AI multi-agente, pipeline RAG, knowledge distillation | main | ❌ assente | ✅ |
| `tools/` | [PYC64](https://github.com/alby69/PYC64) | Compilatore Python→6502, TUI IDE, simulatore | main | ❌ assente | ✅ |
| `tutorial/` | [C64GameTutorial](https://github.com/alby69/C64GameTutorial) | Manuale didattico (27 capitoli), soluzioni, template | main | ❌ assente | ✅ |
| `scraper/` | [C64-Scrapy](https://github.com/alby69/C64-Scrapy) | Scraping documentazione C64, dataset JSONL/Markdown | main | ❌ assente | ✅ |
| `kb-agent/` | [C64-KB-Agent](https://github.com/alby69/C64-KB-Agent) | Knowledge base centralizzata, deduplicazione, indicizzazione | main | ❌ assente | ✅ |
| `debugger/` | [C64-Debugger](https://github.com/alby69/C64-Debugger) | Bridge verso VICE, analisi crash dump, breakpoint | main | `setup.py` | ✅ |
| `editor/` | [C64-Code](https://github.com/alby69/C64-Code) | Tokenizer, diskimage, bridge VICE/Ultimate | main | `pyproject.toml` | ✅ |
| `geckos/` | [C64-OS](https://github.com/alby69/C64-OS) | GeckOS-NG — OS multitasking 6502 | master | ❌ assente | ✅ |
| `gamedev/` | [C64-GameDev](https://github.com/alby69/C64-GameDev) | Kit sviluppo giochi (c64kit + c64lib) | main | `setup.py` | ✅ |

Nota: i 9 submodule risultano tutti presenti in root e il file `.gitmodules` è in corrispondenza 1:1 con le cartelle (Problema #1 del piano di miglioramento già sanato).

## Flusso dati

```
Scrapy (scraper/) ──file JSONL/Markdown──▶ GitHub Actions (cron) ──▶ KB-Agent (kb-agent/)
                                                                          │
                                                                          │ query RAG
                                                                          ▼
                                                                      C64-LLM (core/)
```

Il flusso `Scrapy → GitHub Actions → KB-Agent → LLM` è l'architettura decoupled di riferimento dell'ecosistema: comunica tramite file con ID deterministici SHA256 e deduplicazione esplicita, **senza import di codice Python tra i repository**. Il contratto dati deve essere formalizzato come schema versionato (vedi §5).

Gli altri moduli (`tools/`, `debugger/`, `editor/`, `gamedev/`) sono orchestrati dall'SDK come plugin via CLI/API (vedi §4) e non dipendono l'uno dall'altro a runtime.

## Definizione di plugin

Un componente è un **plugin** dell'SDK se e solo se espone, in `plugins/<nome>/` del wrapper, un manifest `plugin.json` con:

- `name` — identificatore univoco;
- `version` — semver del modulo (indipendente dall'SDK);
- `description`, `category`, `icon`;
- `entry_point` — percorso del wrapper CLI (`plugins/<nome>/wrapper.py`);
- `commands` — lista dichiarativa di comandi con label, descrizione, args e opzioni tipizzate.

L'SDK scopre i plugin in modo dichiarativo (`PluginLoader` in `services/core_service/plugin_loader.py`), li espone via CLI (`make plugins` / `python3 plugins/<nome>/wrapper.py`) e via API REST (`/api/v1/plugins`). Non esiste alcun import diretto del submodule nel codice del wrapper: ogni comando viene eseguito come processo separato.

Stato attuale: **11 plugin** (`ai-agent`, `compiler`, `debugger`, `disk-tools`, `editor`, `emulator`, `geckos`, `game-dev`, `knowledge`, `project-manager`, `tutorial`).

## Contratti dati

I contratti tra componenti devono essere:

1. **versionati** (`schema_version` nei dati stessi);
2. **verificabili** (JSON Schema / Pydantic condiviso, testati su entrambi i lati del contratto);
3. **validati fail-fast** in CI prima che un dato non conforme raggiunga il consumatore.

Contratti noti da formalizzare:

| Produttore | Consumatore | Artefatto |
|---|---|---|
| `scraper/` | `kb-agent/` | frontmatter YAML, JSONL (`scraped_dataset.jsonl`), `knowledge_graph.json`, `api_index.json` |
| `kb-agent/` | `core/` | indice FAISS/SQLite FTS5, schema embedding |
| submodule | SDK | manifest `plugin.json` (§4) |

## Verifica del disaccoppiamento

Prima di considerare un modulo "integrato correttamente", verificare che:

- il modulo si clona da solo (`git clone <url>`);
- il modulo si installa da solo (`pip install .` o `docker compose up` o equivalente);
- il modulo passa i propri test in isolamento (`pytest`);
- l'SDK lo scopre solo tramite manifest e non importa il suo codice direttamente;
- nessun modulo importa un altro modulo dell'ecosistema per path.

## Pinning e versioning

I submodule sono oggi agganciati a branch mobili (`main`, `master` per `geckos`). Per la strategia di pinning su release semantiche e la relativa matrix di compatibilità, vedere `docs/adr/0001-pinning-e-manifest-plugin.md` e la tabella "Compatibility Matrix" nel README.