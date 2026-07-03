# C64 Ecosystem Roadmap

Questo documento delinea il futuro dell'ecosistema C64, consolidando gli obiettivi di integrazione e sviluppo a lungo termine.

## 1. Obiettivi Raggiunti (Milestones)

- [x] **Meta-repository SDK**: Creato C64-Intelligence-SDK per orchestrare l'ecosistema.
- [x] **Disaccoppiamento Core**: Estratte le logiche di validazione (`c64validator`) ed estrazione (`c64extractor`) in package Python indipendenti.
- [x] **Integrazione py6502**: Simulazione e disassemblaggio pure-Python integrati per validazione veloce senza dipendenze esterne.
- [x] **Playground Didattico**: Implementato ambiente REPL per l'apprendimento dell'assembly 6502.
- [x] **Centralizzazione Data Acquisition**: Integrato `C64-Scrapy` come unico fornitore di dati web, eliminando i crawler duplicati nel core.

## 2. Obiettivi a Breve Termine (Fase 2: Consolidamento)

- [ ] **Uniformità Toolchain**: Assicurarsi che tutti i repository (C64-LLM, PYC64, C64GameTutorial) utilizzino esclusivamente i package `c64validator` e `c64extractor`.
- [ ] **Integrazione IDE**: Portare `c64validator` all'interno della TUI di PYC64 per fornire feedback immediato su errori di branch e stima dei cicli.
- [ ] **Mappatura Memoria**: Estendere l'adapter py6502 per mappare le locazioni di memoria C64 più comuni (VIC-II, SID, CIA) per simulazioni più accurate.
- [ ] **Supporto Illegal Opcodes**: Implementare il supporto per gli opcode non documentati del 6502, essenziali per l'analisi di demo e giochi commerciali.

## 3. Obiettivi a Lungo Termine (Fase 3: Servizi Centralizzati)

- [ ] **C64-KB-Service**: Creare un servizio API centralizzato per il RAG (FAISS + Embedding) che possa essere interrogato da qualsiasi componente dell'ecosistema.
- [ ] **C64-Validator-Service**: Esporre le funzionalità di `c64validator` via API per permettere validazioni remote.
- [ ] **Integrazione UI Gradio**: Visualizzare lo stato della CPU e della memoria durante la simulazione direttamente nell'interfaccia Gradio di C64-LLM.
- [ ] **Pipeline Automatica RAG**: Collegare `C64-Scrapy` direttamente al `C64-KB-Service` per aggiornamenti automatici della base di conoscenza.

## 4. Architettura Target

L'obiettivo finale è una struttura modulare dove l'AI (C64-LLM), gli strumenti di sviluppo (PYC64) e le risorse didattiche (C64GameTutorial) poggiano su una base solida di package condivisi e servizi centralizzati, alimentati da un sistema di acquisizione dati professionale (C64-Scrapy).
