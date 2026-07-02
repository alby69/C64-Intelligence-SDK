# Piano di Integrazione py6502 nell'Ecosistema C64

Questo documento descrive come la libreria `py6502` è stata integrata nell'ecosistema C64-Intelligence-SDK per fornire funzionalità di simulazione e disassemblaggio pure-Python.

## 1. Obiettivi
- **Disassemblaggio avanzato**: Migliorare la Knowledge Base (RAG) estraendo codice assembly annotato dai file PRG.
- **Validazione veloce**: Permettere la validazione del codice generato dall'AI senza dipendere da emulatori esterni (VICE) o assembler nativi (ACME) in ambienti limitati.
- **Strumenti didattici**: Fornire un playground interattivo per l'apprendimento dell'assembly 6502.

## 2. Componenti Integrati

### Core (C64-LLM)
- **`core/libs/py6502`**: Libreria originale integrata come modulo interno.
- **`core/utils/py6502_adapter.py`**: Adapter C64-specifico che avvolge il simulatore e il disassemblatore di `py6502`.
- **`core/pipeline/extract_prg.py`**: Potenziato per disassemblare automaticamente le sezioni di codice macchina durante l'estrazione dai PRG.
- **`core/utils/validate_emulator.py`**: Aggiunta la funzione `simulate_asm_code` per testare snippet di codice in una sandbox Python.

### Tools (PYC64)
- **`tools/pyc64c/simulator.py`**: Nuovo strumento a riga di comando per simulare l'esecuzione di file PRG compilati, mostrando lo stato dei registri passo-passo.

### Tutorial (C64GameTutorial)
- **`tutorial/py6502_playground.py`**: Un ambiente interattivo (REPL) dove gli studenti possono scrivere assembly 6502 e vederne immediatamente l'effetto sui registri CPU.

## 3. Workflow d'Uso

### Estrazione Dati per RAG
Eseguendo la pipeline di estrazione su un file PRG, ora si ottiene un listato assembly completo invece di un semplice dump esadecimale:
```bash
python core/pipeline/extract_prg.py gioco.prg
```

### Validazione Codice AI
L'agente Validator può ora usare `simulate_asm_code` per una prima verifica rapida:
```python
from utils.validate_emulator import simulate_asm_code
ok, report = simulate_asm_code(generated_code)
```

### Simulazione PRG
Per testare un programma compilato da PYC64:
```bash
python tools/pyc64c/simulator.py programma.prg
```

## 4. Sviluppi Futuri
- Implementare il supporto per le "Illegal Opcodes" del 6502, comuni nelle demo C64.
- Integrare la visualizzazione della simulazione direttamente nella UI Gradio.
- Estendere l'adapter per mappare le locazioni di memoria C64 più comuni (es. $D020 per il colore del bordo).
