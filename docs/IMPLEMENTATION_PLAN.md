# Piano di Implementazione dell'Ecosistema C64-Intelligence-SDK

Questo documento dettaglia il piano operativo per implementare la Roadmap strategica dell'ecosistema **`C64-Intelligence-SDK`**, con particolare attenzione all'integrazione del nuovo sottomodulo grafico **`C64-GUI`**.

---

## Fase 1: Consolidamento e Standardizzazione delle API (Q3-Q4 2026)
L'obiettivo è garantire che ogni sottomodulo esistente sia esponibile come servizio di rete indipendente con contratti API rigidamente definiti.

### 1.1 Standardizzazione Nomenclatura
- [x] Eliminare riferimenti confusi: `C64PY` indica il linguaggio di programmazione, `PYC64` indica il sottomodulo compilatore/TUI sotto `tools/`.
- [x] Consolidare la documentazione nella cartella `docs/` per riflettere questa nomenclatura uniforme.

### 1.2 Esposizione di PYC64 come Servizio
- [x] Esportare le funzioni core del compilatore (`compile_source`, `compile_to_prg`) in `pyc64c/__init__.py`.
- [x] Implementare la gestione delle richieste SDK strutturate in `pyc64c/sdk.py` per ricevere ed elaborare richieste di compilazione in formato JSON.

### 1.3 Consolidamento C64-KB-Agent
- [x] Garantire il funzionamento di `kb-agent/` come microservizio FastAPI autonomo con API REST per l'indicizzazione dei documenti e la ricerca semantica con FAISS + Sentence-Transformers.

---

## Fase 2: Architettura Multi-Servizio Dockerizzata (Q1 2027)
Configurare l'ambiente in modo che ogni agente venga eseguito in un container Docker dedicato, orchestrato tramite `docker-compose`.

### 2.1 Docker Compose Unificato
- [ ] Aggiornare `docker-compose.yml` nella root del progetto per avviare in modo indipendente `c64-llm-core` (porta 8000), `c64-kb-agent` (porta 8001), `c64-compiler` (porta 8002) e `c64-debugger` (porta 8003).

### 2.2 Test di Integrazione dei Protocolli
- [x] Creare contratti di integrazione automatici in `tests/` per verificare la compatibilità delle risposte JSON dei vari agenti.

---

## Fase 3: Sviluppo di `C64-GUI` Core (Q2 2027)
Avviare lo sviluppo dell'interfaccia grafica centralizzata mantenendo il disaccoppiamento totale.

### 3.1 Progettazione del Layout Visivo dell'IDE
- [ ] Creare un'interfaccia a pannelli (utilizzando Electron o Python-Native come Flet/PySide6) che includa:
  - Esploratore del workspace di file `.c64` e `.asm`.
  - Editor di testo con evidenziazione sintattica.
  - Pannello interattivo per la chat con gli agenti AI di `C64-LLM`.
  - Pannello di monitoraggio dell'emulatore e del debugger.

### 3.2 Client di Rete Asincrono per l'Orchestrazione
- [ ] Implementare la comunicazione asincrona con i sottomoduli tramite socket e REST, in modo che l'interfaccia sia fluida e non si blocchi durante i lunghi compiti di compilazione o addestramento AI.

---

## Fase 4: Integrazione AI Avanzata nella GUI (Q3 2027)
Portare la potenza di `C64-LLM` direttamente all'interno dell'esperienza visiva dello sviluppatore.

### 4.1 Copilot Integrato e Correzione Cliccabile
- [ ] Consentire all'AI di suggerire refactoring o patch di codice direttamente all'interno dell'editor della GUI, con opzione "Applica Modifica" immediata.

### 4.2 Visualizzazione in Tempo Reale del Self-Healing
- [ ] Mostrare graficamente i tentativi asincroni di compilazione, gli errori rilevati e i successivi passaggi eseguiti dall'Orchestrator AI per correggere il codice prima del successo finale.

---

## Fase 5: Consolidamento e Rilascio (Q4 2027)

### 5.1 Rilascio di "CBM-Studio AI"
- [ ] Fornire installatori standalone pre-confezionati o script chiavi in mano (`setup_ecosystem.sh` aggiornato) per avviare l'intero ambiente grafico con un unico comando.
