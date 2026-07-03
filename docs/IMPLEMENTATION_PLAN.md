# Piano di Implementazione PYC64 - SDK Integration

Questo documento dettaglia il piano operativo per implementare la Roadmap di PYC64 e la sua integrazione con il **C64-Intelligence-SDK**.

---

## Fase 1: Fondamenta e Protocollo (Completato/In Corso)

L'obiettivo è trasformare PYC64 in uno strumento programmabile e integrabile.

### 1.1 Esposizione API Programmatica
- [x] Esportare le funzioni core (`compile_source`, `compile_to_prg`) in `pyc64c/__init__.py`.
- [x] Creare documentazione iniziale in `docs/api/README.md`.

### 1.2 Protocollo JSON SDK
- [x] Implementare `pyc64c/sdk.py` per gestire richieste/risposte strutturate.
- [x] Includere metriche (tempo di compilazione, dimensione binario) e diagnostica dettagliata.
- [x] Integrazione con `IntegrationBridge` per feedback loop.

### 1.3 Test Suite e CI/CD
- [x] Creare `tests/test_sdk.py` per validare il protocollo.
- [x] Aggiunti test per la generazione di simboli e diagnostica.

### 1.4 Refactoring Disaccoppiamento
- [x] Implementato `IntegrationBridge` con autodiscovery e dipendenze opzionali.
- [x] Supporto per variabili d'ambiente per configurazione paths.
- [x] Documentazione integrazione SDK completata in `docs/SDK_INTEGRATION.md`.

---

## Fase 2: Potenziamento del Compilatore (Q4 2026)

Migliorare la qualità del codice generato e le capacità del linguaggio.

### 2.1 Ottimizzatore 6502
- **Analisi del Flusso di Controllo**: Implementare un grafo di controllo del flusso (CFG) nell'AST.
- **Pass di Ottimizzazione**:
    - *Constant Folding*: Risolvere espressioni costanti a compile-time.
    - *Dead Code Elimination*: Rimuovere funzioni e variabili non utilizzate.
    - [x] *Zero-Page Allocation*: Ottimizzato l'uso della memoria veloce anche in programmi che usano floating point.
- **Riferimento**: Vedere `pyc64c/code_gen.py` per l'integrazione dei pass.

### 2.2 Supporto Tipi Avanzati
- **Array e Puntatori**: Estendere il parser e il generatore di codice per supportare l'aritmetica dei puntatori e array multidimensionali.
- **Struct/Record**: Introdurre la parola chiave `struct` per definire tipi di dati complessi.

### 2.3 Debug Symbols
- [x] Generare file `.sym` compatibili con VICE per mappare gli indirizzi di memoria ai simboli del codice sorgente.

---

## Fase 3: Integrazione AI-Nativa (Q1 2027)

Sinergia profonda con **C64-LLM**.

### 3.1 Servizio Compiler Agent
- Implementare un server REST (usando FastAPI o Flask) all'interno del container Docker che esponga `process_sdk_request`.
- Endpoint: `POST /compile`.

### 3.2 Feedback Loop Strutturato
- Estendere il formato JSON dei `diagnostics` per includere suggerimenti per l'AI (es. "Possible type mismatch at line X, try casting to byte").
- Implementare il "self-healing" dove l'Orchestrator riceve questi suggerimenti e corregge il codice.

---

## Fase 4: Dataset e Scalabilità (Q2 2027)

### 4.1 Generazione Dataset per Fine-tuning
- Creare uno script che compila migliaia di esempi `.c64` e cattura le coppie (Sorgente -> Assembly 6502).
- Utilizzare questi dati per il fine-tuning dei modelli linguistici specializzati nel C64.

### 4.2 Multi-target Support
- Astrarre il backend di generazione del codice in `pyc64c/code_emitter.py` per supportare altre CPU 6502 (Atari, Apple II).

---

## Collegamento con C64-Intelligence-SDK

PYC64 agisce come il braccio operativo ("Tool") per l'agente Coder del SDK:
1. **Coder Agent** scrive il codice `.c64`.
2. **PYC64 Agent** lo compila e restituisce il binario o gli errori.
3. **Validator** usa i metadati e i simboli generati da PYC64 per verificare la correttezza nel simulatore.
