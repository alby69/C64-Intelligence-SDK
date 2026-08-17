# ADR-0002 — Contratto dati versionato tra i moduli

- **Data**: 2026-08-17
- **Stato**: adottata
- **Contesto**: [CONTRACT.md](../../kb-agent/CONTRACT.md), Epic B

## Decisione

1. **`C64-KB-Agent` è il titolare del contratto dati.** Gli schemi JSON risiedono in `kb-agent/schemas/` e sono l'unico artefatto condiviso tra i produttori e i consumatori di dati.

2. **Nessun import di codice tra i repository coinvolti.** `C64-Scrapy` (produttore) e `C64-KB-Agent` (consumatore) comunicano tramite file la cui struttura è versionata e validata con `jsonschema` su **entrambi i lati**, fail-fast in CI.

3. **Versionamento tollerante.** `schema_version` nel frontmatter; se assente si assume `1`. Ciò permette transizioni graduali tra versioni dello schema senza rompere i dati storici.

## Contratti coperti

- Contratto 1: Scrapy → KB-Agent (documenti Markdown, JSONL, knowledge graph, API index).
- Contratto 2: KB-Agent → C64-LLM (percorso `data/docs/**/*.md`, frontmatter e body; l'indice FAISS è generato dal consumatore localmente).
- Contratto 3: submodule → SDK (manifest `plugin.json`, vedi ADR-0001).

## Conseguenze

- Divergenza nota `tags` (C64-LLM) vs `topics` (Scrapy) da risolvere allineando il consumatore o introducendo `tags` come alias nello schema v2.
- Il produttore valida i documenti prima del push; il consumatore rifiuta i non conformi invece di indicizzarli.