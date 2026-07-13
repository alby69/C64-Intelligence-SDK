# C64-Intelligence-SDK — Sistema di Automazione Submodule

Questo pacchetto automatizza il workflow multi-repo descritto nel documento **IMPLEMENTATION_SPEC_AND_GUIDE.md** (Paragrafo 2), eliminando la necessita di comandi git manuali per spostarsi tra i repository dei submodule.

## Prerequisito: configurare `.gitmodules`

Affinche lo script funzioni correttamente, ogni submodule deve dichiarare il branch in `.gitmodules`:

```ini
[submodule "core"]
    path = core
    url = https://github.com/alby69/C64-LLM.git
    branch = main
[submodule "tools"]
    path = tools
    url = https://github.com/alby69/PYC64.git
    branch = main
[submodule "tutorial"]
    path = tutorial
    url = https://github.com/alby69/C64GameTutorial.git
    branch = main
[submodule "scraper"]
    path = scraper
    url = https://github.com/alby69/C64-Scrapy.git
    branch = main
```

## Installazione

Copia i file nella root del repository collettore:

```bash
cp submodule-manager.py scripts/
cp update-submodules.sh scripts/
cp docker-compose.override.yml .
cp Dockerfile.updater .
chmod +x scripts/update-submodules.sh
chmod +x scripts/submodule-manager.py
```

## Comandi

### Scenario B — Aggiornamento da remoto (documento, par. 2)

Hai lavorato su un repo separato (es. C64-LLM), hai fatto push su GitHub e ora vuoi "riagganciare" le modifiche nel collettore:

```bash
# Via Docker (consigliato)
docker compose run --rm sdk-updater update

# Aggiorna e pusha il collettore
docker compose run --rm sdk-updater update --push

# Forza l'update anche se ci sono modifiche locali non committate
docker compose run --rm sdk-updater update --force
```

### Scenario A — Sviluppo locale nei submodule (documento, par. 2)

Hai modificato i file direttamente dentro `core/` o `tools/` e vuoi committare e pushare tutto:

```bash
# Commit e push automatici di tutti i submodule dirty, poi aggiorna il parent
docker compose run --rm sdk-updater dev-sync -m "feat: nuova integrazione VICE"

# Come sopra ma pusha anche il collettore
docker compose run --rm sdk-updater dev-sync -m "feat: nuova integrazione VICE" --push
```

### Utility

```bash
# Stato di tutti i submodule (branch, commit, modifiche)
docker compose run --rm sdk-updater status

# Sincronizza URL da .gitmodules
docker compose run --rm sdk-updater sync

# Reset di emergenza (torna ai commit tracciati dal parent)
docker compose run --rm sdk-updater reset
docker compose run --rm sdk-updater reset --hard
```

### Esecuzione nativa (senza Docker)

```bash
./scripts/update-submodules.sh update --push
./scripts/update-submodules.sh dev-sync -m "fix: bug raster"
./scripts/update-submodules.sh status
```

## Cosa fa automaticamente lo script

1. **Rileva detached HEAD**: se un submodule e in stato detached (come succede dopo `git submodule update`), lo script crea/checkout il branch corretto e imposta il tracking con `origin/<branch>`.
2. **Fetch remoto**: esegue `git fetch origin` per ogni submodule.
3. **Merge**: esegue `git merge origin/<branch>` portando i nuovi commit.
4. **Gestione conflitti**: se un merge fallisce, abortisce automaticamente e segnala l'errore senza lasciare il repository in uno stato sporco.
5. **Commit parent**: esegue `git add <submodule>` nel collettore e crea un commit con messaggio standardizzato (`chore(submodules): aggiorna <path> a <commit>`).
6. **Push opzionale**: se usi `--push`, pusha il collettore su origin.

## Integrazione CI/CD

Puoi aggiungere uno step GitHub Actions:

```yaml
- name: Aggiorna Submodule
  run: docker compose run --rm sdk-updater update --push
```

## Vantaggi rispetto al workflow manuale

- **Zero `cd` nei submodule**: non devi mai entrare manualmente in `core/`, `tools/`, ecc.
- **Zero gestione branch**: lo script risolve automaticamente detached HEAD e tracking.
- **Atomicita**: ogni submodule aggiornato viene immediatamente registrato nel collettore.
- **Docker-native**: funziona identicamente in locale, su server e in CI/CD.
- **Safe defaults**: non perde mai modifiche locali senza esplicito `--force`.
