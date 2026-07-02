# Guida alla Gestione Git per PYC64

Questa guida spiega come gestire il repository PYC64, come consolidare il lavoro e come separarsi definitivamente dal fork originale (C64C).

## 1. Stato Attuale e Relazione con C64C

Il progetto **PYC64** è un'evoluzione sostanziale di **C64C**. Mentre C64C usava una sintassi simile al C, PYC64 implementa un compilatore per un sottoinsieme di **Python**.

**Ha senso il fork?**
Assolutamente sì. Il codice è stato quasi completamente riscritto (`pyc64c/` invece di `c64c/`), con un nuovo lexer, parser e runtime. Non è più compatibile con il progetto originale, quindi procedere in autonomia è la scelta corretta.

## 2. Come "Sganciarsi" dal Fork Iniziale

Se il tuo repository su GitHub è ancora segnato come "forked from YouDevIt/C64C" e vuoi rimuovere questo legame:
1. **Contatta il supporto di GitHub** chiedendo di "unfork" il repository (mantenendolo come repository indipendente).
2. Oppure: Crea un nuovo repository vuoto e pusha il tuo codice lì.

Dal punto di vista tecnico (Git locale):
- Assicurati di non avere un remote chiamato `upstream` che punta a C64C:
  ```bash
  git remote remove upstream
  ```
- Il tuo `origin` deve essere `https://github.com/alby69/PYC64`.

## 3. Gestione dei Rami (Branches)

Durante lo sviluppo sono stati creati molti rami (`feat-*`, `refactor-*`). Ora che il progetto è stabile, è bene consolidare tutto nel `main`.

### Come fare il Merge correttamente nel Main
Se hai lavorato su un ramo chiamato `nuova-feature`:
1. Torna sul main: `git checkout main`
2. Scarica le ultime modifiche: `git pull origin main`
3. Unisci il ramo: `git merge nuova-feature`
4. Se ci sono conflitti, risolvili e fai il commit.
5. Carica online: `git push origin main`

### Pulizia dei rami obsoleti
Dopo il merge, elimina il ramo che non serve più:
```bash
# Elimina locale
git branch -d nome-ramo
# Elimina remoto (su GitHub)
git push origin --delete nome-ramo
```

## 4. Workflow Suggerito per PYC64

1. **Sempre su `main` per le piccole correzioni.**
2. **Usa rami temporanei per grandi feature**, ma fai il merge appena funzionano.
3. **Evita rami "fantasma"**: se un ramo come `feat-c64-graphics-api` è stato integrato nel main, cancellalo subito sia in locale che su GitHub per non creare confusione.

---
*Nota: Ho già consolidato le ultime modifiche alle API Graphics e Sound nel tuo ramo `main` locale.*
