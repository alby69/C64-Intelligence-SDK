# C64-ReadyCode-Py (`readycode_py`)

Questo modulo Python è un porting nativo delle logiche core di **READYCode (C64Code)**, originariamente sviluppato in C#/.NET da Moonspace Labs, LLC e jbramwell.

## Caratteristiche Portate
- **Tokenizer & PRG Converter**: Tokenizzazione di sorgenti C64 BASIC V2, supporto delle abbreviazioni di tastiera (shift-abbreviations), detokenizzazione e rilevamento di file BASIC reali tramite validazione della struttura dei puntatori.
- **Disk Image Editor**: Parser e editor di immagini disco `.d64` e `.d81` con gestione della BAM, allocazione e deallocazione dei settori, lettura ed estrazione di file, ridenominazione, eliminazione e rimpiazzo dei file in conformità con CBM DOS.
- **Client di Rete**:
  - REST client per C64 Ultimate (load/run PRG, comandi di macchina, mount/eject dischi).
  - FTP client per esplorazione di C64 Ultimate.
  - Client binary monitor per emulatore VICE (TCP).
- **Trasformazioni di Codice**: Minify e Prettify del codice BASIC C64.

## Crediti e Licenze
- **Progetto Originale**: [READYCode](https://github.com/jbramwell/READYCode) (Moonspace Labs, LLC), licenza MIT.
- **Fork di Riferimento**: [C64Code](https://github.com/alby69/C64Code) (Alberto Abate), licenza MIT.
- **Questo Modulo**: Rilasciato sotto licenza GPLv3 all'interno del progetto **C64-Intelligence-SDK**. Il porting mantiene la compatibilità di licenza ed esprime i dovuti crediti agli autori originali.
