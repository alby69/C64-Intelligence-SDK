# Changelog

Tutte le modifiche rilevanti di questo progetto saranno documentate in questo file.
Formato basato su [Keep a Changelog](https://keepachangelog.com/it/1.1.0/) e [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Aggiunto
- Submodule `gamedev/` (C64-GameDev) con plugin `game-dev`.
- Schema contratto dati (Epic B): `kb-agent/schemas/*.json` + test di validazione su produttore e consumatore.
- Manifest `plugin.yaml` nei sub-repo e `pyproject.toml` per core/tools/scraper/kb-agent (Epic C).
- CI SDK (`sdk-ci.yml`): verifica integrità submodule, test plugin system (Epic A).
- `ARCHITECTURE.md`, `SECURITY.md`, `THIRD_PARTY_LICENSES.md`, ADR-0001.

## [0.0.1] - 2026-07-28

### Aggiunto
- Prima versione dell'SDK con 8 submodule e plugin system.