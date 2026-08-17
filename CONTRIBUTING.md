# Contributing — C64-Intelligence-SDK

Grazie per contribuire all'ecosistema C64 Intelligence SDK.

## Principio architetturale

**"Standalone-first, Integrated-second"** (vedi `ARCHITECTURE.md`): i submodule devono restare clonabili, installabili, testabili e usabili da soli. L'SDK li orchestra dichiarativamente tramite manifest `plugin.json`. Non aggiungere mai import diretti tra submodule o logica di dominio nel wrapper.

## Modifiche ai puntatori submodule

Ogni PR che tocca un puntatore submodule (un nuovo SHA in `core/`, `tools/`, …) deve:

1. aggiornare la **Compatibility Matrix** nel README;
2. eseguire **`tests/integration/`** (compile round-trip, contratto KB, query KB) prima del merge;
3. passare la CI `sdk-ci.yml`, che verifica l'integrità submodule e il plugin system.

## Workflow di sviluppo

```bash
git submodule update --init --recursive
make setup
make plugin-test     # test plugin system
python -m pytest tests/integration/   # test e2e
```

## Standard richiesti

- **Nessun segreto** nel codice o nei log di CI.
- Test automatici per ogni nuovo contratto dati (schema JSON condiviso).
- Aggiornare `CHANGELOG.md` per modifiche rilevanti.
- Un submodule modificato va committato nel suo repository prima di bumpare il puntatore nell'SDK.