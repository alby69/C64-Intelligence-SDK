# Guida all'Integrazione del C64-Intelligence-SDK

Questa guida descrive come i vari agenti e sottomoduli dell'ecosistema **C64-Intelligence-SDK** cooperano, scambiano dati e mantengono un'architettura rigorosamente disaccoppiata (*loose coupling*).

---

## 1. Nomenclatura Standard dell'Ecosistema

Per evitare ambiguità nella documentazione e nel codice, viene stabilito lo standard terminologico seguente:

*   **`C64-Intelligence-SDK`**: Il repository padre e il framework di sviluppo complessivo. Coordina l'ecosistema e gestisce l'integrazione di tutti i sottomoduli.
*   **`C64PY`** (o **C64-Python** / **`.c64`**): Il linguaggio di programmazione ad alto livello ispirato a Python, arricchito con annotazioni di tipo, destinato alla compilazione in codice nativo Commodore 64.
*   **`PYC64`**: Il sottomodulo di compilazione, assembler e ambiente TUI (posizionato sotto `tools/`). Fornisce il compilatore di backend (`pyc64c`) e l'editor di testo testuale (`pyc64_ui`).
*   **`C64-LLM`** (posizionato in `core/`): L'agente multi-agente e sistema di ragionamento centrale. Coordina il ciclo di generazione codice (*Coder*), ricerca semantica (*Researcher*), convalida (*Validator*) e correzione automatica (*Self-Healing*).
*   **`C64-KB-Agent`** (posizionato in `kb-agent/`): L'agente di Knowledge Base semantica che espone servizi di indicizzazione vettoriale, ricerca semantica (RAG) e risoluzione degli indirizzi hardware fisici.
*   **`C64-Debugger`** (posizionato in `debugger/`): L'agente dedicato al debugging dinamico e all'interfacciamento bidirezionale con l'emulatore VICE tramite protocollo monitor.
*   **`C64-Scrapy`** (posizionato in `scraper/`): L'agente di scraping specializzato per estrarre informazioni e sorgenti storiche da portali web ed alimentare la Knowledge Base.
*   **`C64-GUI`**: La proposta di nuova interfaccia grafica unificata (simile a VSCode o CBM Studio) per orchestrare l'intero ecosistema.

---

## 2. Flusso e Architettura di Integrazione

L'integrazione tra i moduli avviene esclusivamente tramite chiamate di rete standard, evitando import Python diretti fra sottomoduli diversi. Questo garantisce che ogni agente possa essere distribuito ed eseguito in isolamento (es. tramite container Docker dedicati).

```
 ┌────────────────────────────────────────────────────────┐
 │                      C64-GUI                           │
 └──────────────────────────┬─────────────────────────────┘
                            │ (Orchestra l'esperienza utente)
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │                      C64-LLM                           │
 │        (Generazione, Ragionamento & Self-Healing)      │
 └──────┬───────────────────┬─────────────────────┬───────┘
        │                   │                     │
        │ (Query RAG)       │ (Compilazione)      │ (Esecuzione e Verifica)
        ▼                   ▼                     ▼
 ┌──────────────┐    ┌──────────────┐      ┌──────────────┐
 │ C64-KB-Agent │    │    PYC64     │      │ C64-Debugger │
 │ (kb-agent/)  │    │  (tools/)    │      │  (debugger/) │
 └──────────────┘    └──────────────┘      └──────────────┘
```

---

## 3. Protocolli di Scambio (JSON Contract)

### 3.1 Compilazione (`PYC64` Service)

Il compilatore `PYC64` espone un servizio REST che elabora sorgenti `C64PY` (.c64) o Assembly (.asm) e restituisce binari PRG, listing assembler e mappe dei simboli.

*   **Endpoint**: `POST /compile`
*   **Contratto Richiesta**:

```json
{
  "source_code": "def main() -> byte:\n    border_color(0)\n    return 0",
  "options": {
    "optimize": true,
    "generate_symbols": true
  }
}
```

*   **Contratto Risposta (Successo)**:

```json
{
  "status": "success",
  "artifacts": {
    "prg_base64": "S3kABA==...",
    "listing": "; Listing ASM\nORG $080D...",
    "symbols": "main=$080d\n"
  },
  "metrics": {
    "compile_time_ms": 25,
    "binary_size_bytes": 12
  }
}
```

### 3.2 Ciclo di Auto-Guarigione (Self-Healing)

Se la compilazione fallisce, il compilatore restituisce diagnostiche dettagliate con codice di errore strutturato. L'Orchestrator di `C64-LLM` intercetta queste diagnostiche, le inietta nel prompt del modello generatore (Coder) e richiede una versione corretta del codice.

*   **Contratto Risposta (Errore)**:

```json
{
  "status": "error",
  "diagnostics": [
    {
      "severity": "error",
      "line": 2,
      "column": 5,
      "message": "Name 'border_colorr' is not defined. Did you mean 'border_color'?",
      "source": "compiler-linter"
    }
  ]
}
```

---

## 4. Integrazione Dinamica tramite `IntegrationBridge`

Per consentire l'esecuzione locale e agevolare lo sviluppo, `PYC64` (in `tools/pyc64c/integration.py`) include un modulo `IntegrationBridge`.

Questo ponte di integrazione:
1.  **Rileva automaticamente la root del SDK** tramite la ricerca dinamica di directory o la variabile d'ambiente `C64_SDK_ROOT`.
2.  **Carica pacchetti condivisi** situati all'interno della directory root per non duplicare la logica (es. validatori di codice o simulatori pure-Python).
3.  **Risolve gli esempi** presenti in `C64GameTutorial` (`tutorial/`) per usarli come suite di test funzionali o materiale per il RAG.

### Esempio di utilizzo programmatico del Bridge

```python
from pyc64c.integration import get_bridge

# Ottiene l'istanza del bridge (singleton)
bridge = get_bridge()

# Verifica se il validatore condiviso del SDK è accessibile
validator = bridge.get_validator()
if validator:
    result = validator.validate_prg("output.prg")
    print(f"Esito validazione: {result}")
```

---

## 5. Configurazione dell'Ambiente

I moduli leggono le impostazioni di integrazione tramite le seguenti variabili d'ambiente:

*   `C64_SDK_ROOT`: Percorso assoluto della cartella principale del `C64-Intelligence-SDK`.
*   `C64_FEEDBACK_DIR`: Directory in cui salvare i log e i file di feedback JSON dell'esecuzione degli agenti (predefinito: `/tmp/c64_feedback`).
*   `C64_KB_URL`: URL del microservizio `C64-KB-Agent` (predefinito: `http://localhost:8001`).
*   `C64_COMPILER_URL`: URL del servizio di compilazione `PYC64` (predefinito: `http://localhost:8002`).
