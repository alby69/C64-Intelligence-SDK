# Security Policy

## Versioni supportate

Le correzioni di sicurezza vengono applicate al ramo `main` del repository wrapper. I submodule (`core/`, `tools/`, `tutorial/`, `scraper/`, `kb-agent/`, `debugger/`, `editor/`, `geckos/`, `gamedev/`) sono repository indipendenti: ogni vulnerabilità in essi va segnalata al rispettivo repository e verificata al momento del bump del puntatore submodule.

## Segnalazione di una vulnerabilità

**Non aprire issue pubbliche per problemi di sicurezza.**

Inviare il report via email al maintainer:

- **Alberto Abate** — alberto.abate@gmail.com

Nel report includere:

1. descrizione del problema e impatto;
2. componente interessato (SDK o submodule specifico, con SHA del puntatore);
3. passo-passo di riproduzione;
4. eventuale patch proposta.

## Tempi di risposta

Entro **7 giorni** viene confermata la ricezione del report. La risoluzione e l'annuncio seguono la pratica della responsible disclosure: le correzioni vengono pubblicate senza dettagli di sfruttamento prima del rilascio della fix.

## Segreti e automazioni

Le automazioni cross-repo (es. push `scraper/` → `kb-agent/`) devono usare token a privilegi minimi (GitHub App o Fine-Grained PAT con scope limitato al singolo repository target), mai PAT con scope `repo` ampio. Nessun segreto deve comparire nei file del repository o nei log di CI.