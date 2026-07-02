# Strategia di Disaccoppiamento e Integrazione C64 Ecosystem

Questo documento delinea la strategia per disaccoppiare i moduli core dall'assistente AI (C64-LLM) e permetterne il riutilizzo in tutto l'ecosistema (PYC64, C64GameTutorial).

## 1. Obiettivi
- **Modularità**: Estrarre logiche generiche (validazione, estrazione, crawling) in package Python indipendenti.
- **Riutilizzo**: Permettere agli altri repository di usare gli stessi strumenti di validazione dell'AI.
- **Semplificazione**: Ridurre il peso di C64-LLM delegando funzioni non-AI a moduli dedicati.

## 2. Nuovi Moduli Proposti

### [C64-Validator] (Package Python)
*Estratto da: core/utils/*
- **Funzionalità**: Wrapper ACME, Parser BASIC v2, Cycle Counter, Simulatore py6502.
- **Uso**: C64-LLM (per validare output AI), PYC64 (per validare codice generato), C64GameTutorial (per testare soluzioni).

### [C64-Extractor] (Package Python)
*Estratto da: core/pipeline/*
- **Funzionalità**: `extract_prg.py`, `extract_d64.py`, `extract_g64.py`, detokenizer BASIC.
- **Uso**: Ingestion per RAG, tool di esplorazione file per l'utente.

### [C64-KB-Service] (Servizio API)
*Estratto da: core/knowledge_base/ + RAG*
- **Funzionalità**: Centralizza FAISS, embedding, ricerca semantica.
- **Uso**: Tutti i repository possono interrogare la documentazione tecnica via API.

## 3. Roadmap di Integrazione

### Fase 1: Estrazione (In corso in questo repo)
1. Creare la struttura `packages/` nel root del SDK.
2. Spostare `core/utils/py6502_adapter.py` e logiche correlate in `packages/c64validator`.
3. Spostare le pipeline di estrazione in `packages/c64extractor`.

### Fase 2: Refactoring Repository Submodule
1. **C64-LLM**: Rimuovere le utility interne e importarle dai nuovi package.
2. **PYC64**: Integrare `c64validator` per fornire feedback immediato nell'IDE.
3. **C64GameTutorial**: Sostituire gli script di validazione custom con `c64validator`.

### Fase 3: Centralizzazione Data Acquisition
1. Delegare tutto lo scraping a **C64-Scrapy**.
2. Rimuovere `c64_asm_scraper.py` da C64-LLM.
3. Configurare C64-Scrapy per alimentare direttamente il `C64-KB-Service`.

## 4. Stato Attuale (C64-Intelligence-SDK)
- [x] Integrazione `py6502` come libreria pura-Python per validazione veloce.
- [x] Adapter C64-specifico creato.
- [x] Playground didattico implementato.
- [ ] Estrazione formale dei package in `packages/`.
