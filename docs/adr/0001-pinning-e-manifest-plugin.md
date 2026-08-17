# ADR-0001 — Manifest dei plugin e strategia di pinning

- **Data**: 2026-08-17
- **Stato**: adottata
- **Contesto**: [ARCHITECTURE.md](../../ARCHITECTURE.md)

## Decisione

1. **Manifest di plugin dichiarativo.** Ogni componente dell'ecosistema resta autonomo; l'integrazione nell'SDK avviene esclusivamente tramite un manifest `plugins/<nome>/plugin.json` nel repo wrapper (`name`, `version`, `description`, `category`, `icon`, `entry_point`, `commands`), scoperto da `PluginLoader` in `services/core_service/plugin_loader.py`. Nessun import diretto del codice di un submodule nel wrapper; ogni comando è eseguito come processo separato.

2. **Pinning a tag semantico per i rami stabili.** I submodule oggi seguono branch mobili (`main`, `master` per `geckos`). Per ridurre il rischio di breaking change silenziose, il ramo `main` dell'SDK deve puntare a **tag `v*` semantici** dei submodule, con un eventuale ramo `dev`/`edge` dell'SDK che segue `main` dei submodule per lo sviluppo attivo. La matrix di compatibilità è pubblicata nel README e verificata in CI.

## Conseguenze

- Il wrapper non contiene logica di dominio (principio "Standalone-first, Integrated-second").
- Un bump del puntatore submodule passa obbligatoriamente dalla CI di integrazione SDK prima del merge.
- La corrispondenza `.gitmodules` ↔ albero è verificata automaticamente in CI.