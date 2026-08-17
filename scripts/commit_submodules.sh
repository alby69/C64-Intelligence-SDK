#!/usr/bin/env bash
# commit_submodules.sh — Committa e (opzionalmente) pusha le modifiche Epic
# nei sub-repo dell'SDK, poi aggiorna i puntatori gitlink nel wrapper.
#
# Uso:
#   bash scripts/commit_submodules.sh           # solo commit nei sub-repo
#   bash scripts/commit_submodules.sh --push    # commit + push + bump wrapper
set -euo pipefail

SDK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUSH="${1:-}"
MESSAGE="Architettura a plugin e contratti dati (Epic B-C): plugin.yaml, pyproject.toml, schemi JSON contratto, CHANGELOG, governance (SECURITY/CODEOWNERS/dependabot), test di validazione"

# nome -> messaggio dedicato (overkill generico qui, ma leggibile)
declare -A CUSTOM=(
  [kb-agent]="Epic B-C: contratti dati versionati (schemas/), test validazione, fix dati non conformi (title vuoti), pyproject.toml, plugin.yaml, CONTRACT.md, dedup test, governance"
  [scraper]="Epic B-C: test contratto dati lato produttore, pyproject.toml, plugin.yaml, CHANGELOG, governance"
  [tools]="Epic C-H: pyproject.toml, plugin.yaml, note fork upstream, CHANGELOG, governance"
  [core]="Epic C-H: pyproject.toml, plugin.yaml, scripts/setup_model.sh (checksum), CHANGELOG, governance"
)

cd "$SDK_ROOT"

for d in core tools tutorial scraper kb-agent debugger editor geckos submodules/c64-gamedev; do
  if [ ! -d "$d/.git" ]; then
    echo "[SKIP] $d: non è un submodule inizializzato"
    continue
  fi
  if [ -z "$(git -C "$d" status --porcelain)" ]; then
    echo "[OK]   $d: nessuna modifica"
    continue
  fi
  msg="${CUSTOM[$d]:-$MESSAGE}"
  echo "[...] $d: commit"
  git -C "$d" add -A
  git -C "$d" commit -m "$msg" || echo "[WARN] $d: commit fallito (vuoto?)"
  if [ "$PUSH" = "--push" ]; then
    branch="$(git -C "$d" rev-parse --abbrev-ref HEAD)"
    echo "[...] $d: push origin/$branch"
    git -C "$d" push origin "$branch"
  fi
done

if [ "$PUSH" = "--push" ]; then
  echo "[...] wrapper: aggiorna puntatori submodule"
  git add core tools tutorial scraper kb-agent debugger editor geckos submodules/c64-gamedev
  echo "[OK] Puntatori aggiornati. Verifica con: git status, poi commit nel wrapper."
fi