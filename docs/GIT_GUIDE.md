# Guida alla Gestione Git per C64-Intelligence-SDK

Questa guida spiega come gestire il flusso di lavoro Git all'interno del repository padre **`C64-Intelligence-SDK`** e dei suoi sottomoduli collegati (`core/`, `tools/`, `kb-agent/`, `debugger/`, `scraper/`, `tutorial/`).

---

## 1. Architettura dei Sottomoduli Git

Il repository `C64-Intelligence-SDK` adotta un'architettura modulare in cui ciascun agente o strumento risiede in un proprio repository GitHub indipendente ed è collegato come **Git Submodule** nel repository padre.

Questa separazione garantisce un disaccoppiamento forte e consente a ciascun sottomodulo di essere sviluppato, testato e rilasciato in autonomia.

### Mappa dei Sottomoduli

| Percorso Locale | Repository GitHub | Descrizione |
|---|---|---|
| `core/` | [C64-LLM](https://github.com/alby69/C64-LLM) | Agente multi-agente e RAG vettoriale |
| `tools/` | [PYC64](https://github.com/alby69/PYC64) | Compilatore `C64PY`, TUI e simulatore 6502 |
| `kb-agent/` | [C64-KB-Agent](https://github.com/alby69/C64-KB-Agent) | Servizio di indicizzazione e Knowledge Base |
| `debugger/` | [C64-Debugger](https://github.com/alby69/C64-Debugger) | Agente di debug e monitor VICE |
| `scraper/` | [C64-Scrapy](https://github.com/alby69/C64-Scrapy) | Web scraping e acquisizione dati |
| `tutorial/` | [C64GameTutorial](https://github.com/alby69/C64GameTutorial) | Tutorial educativi ed esempi |

---

## 2. Comandi Essenziali per i Sottomoduli

### Inizializzazione iniziale dell'ambiente
Quando cloni per la prima volta il repository padre `C64-Intelligence-SDK`, le cartelle dei sottomoduli saranno inizialmente vuote. Per scaricare ed allineare tutto il codice:

```bash
git submodule update --init --recursive
```

### Aggiornare tutti i sottomoduli all'ultima versione (dalle rispettive origini)
Se vuoi scaricare le ultime modifiche apportate ai rami `main` dei singoli repository remoti dei sottomoduli:

```bash
git submodule update --remote --merge
```

### Controllare lo stato dei sottomoduli
Per verificare se i sottomoduli locali hanno modifiche non committate o se puntano a commit diversi da quelli registrati nel repository padre:

```bash
git submodule status
```

---

## 3. Workflow di Sviluppo Consigliato

Quando devi apportare modifiche all'ecosistema, segui questi passaggi per mantenere allineati il repository padre e i sottomoduli:

### Passaggio 1: Modifica e commit all'interno del sottomodulo
Entra nella cartella del sottomodulo interessato (es. `tools/`), apporta le modifiche, esegui i test, e crea un commit locale:

```bash
cd tools/
git checkout main
# ... apporta le modifiche ...
git add .
git commit -m "feat: aggiunto supporto per nuove funzioni grafiche"
git push origin main
```

### Passaggio 2: Allineamento del Repository Padre
Torna nella cartella principale (`C64-Intelligence-SDK`). Noterai che Git rileva un cambiamento nel sottomodulo (il sottomodulo ora punta a un nuovo commit hash). Crea un commit nel repository padre per registrare questo aggiornamento:

```bash
cd ..
git status
# Vedrai qualcosa come: modified:   tools (new commits)
git add tools
git commit -m "chore: aggiornato sottomodulo tools (PYC64)"
git push origin main
```

---

## 4. Evitare il problema del "Detached HEAD"

Spesso, eseguendo `git submodule update`, Git sposta i sottomoduli in uno stato di "Detached HEAD" (ovvero non associati ad alcun ramo attivo, come `main`).

**Come evitare errori:**
Prima di iniziare a scrivere codice all'interno di una cartella sottomodulo, assicurati sempre di posizionarti sul ramo principale:

```bash
cd tools/
git checkout main
```
o in alternativa, configura Git per aggiornare i sottomoduli eseguendo automaticamente il merge sul ramo registrato:
```bash
git submodule update --remote --merge
```
