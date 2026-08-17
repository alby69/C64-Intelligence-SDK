# Terze parti e licenze

Questo repository (C64-Intelligence-SDK) è un meta-repository GPLv3 che aggrega, come Git submodule, componenti indipendenti. La tabella seguente elenca la licenza di ogni componente incluso e gli obblighi che ne derivano per chi redistribuisce l'SDK completo.

| Componente | Repository | Licenza | Note |
|---|---|---|---|
| SDK (wrapper) | [C64-Intelligence-SDK](https://github.com/alby69/C64-Intelligence-SDK) | **GPLv3** | vedere `LICENSE` |
| `core/` | [C64-LLM](https://github.com/alby69/C64-LLM) | **GPLv3** | `core/LICENSE` |
| `tools/` | [PYC64](https://github.com/alby69/PYC64) | **GPLv3** | `tools/LICENSE`; fork di [YouDevIt/C64C](https://github.com/YouDevIt/C64C) — verificare gli obblighi upstream ereditati |
| `tutorial/` | [C64GameTutorial](https://github.com/alby69/C64GameTutorial) | **CC BY 4.0** (manuale) / **MIT** (codice `.asm`) | nessun file LICENSE in root; dichiarazione nel README del submodule |
| `scraper/` | [C64-Scrapy](https://github.com/alby69/C64-Scrapy) | **GPLv3** | `scraper/LICENSE` |
| `kb-agent/` | [C64-KB-Agent](https://github.com/alby69/C64-KB-Agent) | **GPLv3** | `kb-agent/LICENSE` |
| `debugger/` | [C64-Debugger](https://github.com/alby69/C64-Debugger) | **GPLv3** | `debugger/LICENSE` |
| `editor/` | [C64-Code](https://github.com/alby69/C64-Code) | **MIT** | `editor/LICENSE`; © Moonspace Labs, LLC |
| `geckos/` | [C64-OS](https://github.com/alby69/C64-OS) | **GPLv2** | `geckos/COPYING` |
| `gamedev/` | [C64-GameDev](https://github.com/alby69/C64-GameDev) | **da definire** | nessun file LICENSE presente — aggiungere prima del rilascio |

## Obblighi di redistribuzione

- **GPLv3/GPLv2 (copyleft forte)**: chi redistribuisce l'SDK (binario o sorgente aggregato) deve rilasciarlo sotto la stessa licenza, rendere disponibile il codice sorgente e preservare le note di copyright.
- **MIT**: consente l'uso con attribuzione; nessun obbligo copyleft.
- **CC BY 4.0** (manuale `tutorial/`): richiede l'attribuzione dell'autore originale (`@alby69`) quando si redistribuisce il materiale didattico; non si applica al codice.

I componenti non ancora licenziati (`gamedev/`) o con licenza mista (`tutorial/`) vanno chiariti prima di pubblicare release distributive dell'SDK.

## Dipendenze di terze parti

Le dipendenze Python/NPM dei singoli componenti sono gestite nei rispettivi `requirements.txt`/`pyproject.toml`/`package.json`. Il monitoraggio delle vulnerabilità delle dipendenze è previsto via Dependabot a livello di ciascun sub-repo (vedi `SECURITY.md`).