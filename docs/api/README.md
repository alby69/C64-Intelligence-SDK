# Documentazione delle API Programmatiche di PYC64

## Panoramica

Il modulo **`PYC64`** fornisce un'API Python per compilare codice sorgente scritto in **`C64PY`** (Python-like) direttamente in formato binario nativo Commodore 64 (`.PRG`) e BASIC.

Per una visione d'insieme della strategia di sviluppo a lungo termine e dell'integrazione, consultare la [Guida all'Integrazione](../SDK_INTEGRATION.md) e il [Piano di Implementazione](../IMPLEMENTATION_PLAN.md).

## Moduli Principali

### `pyc64c.compiler`

*   `compile_source(src: str) -> CompileResult`: Esegue l'analisi lessicale e sintattica del codice sorgente `C64PY`.
*   `compile_to_prg(src: str) -> (bytes, CompileResult)`: Compila il codice sorgente direttamente in byte prg pronti per l'esecuzione.

### `pyc64c.sdk`

*   `process_sdk_request(request_json: str) -> str`: Elabora le richieste JSON in arrivo dagli altri agenti del `C64-Intelligence-SDK` secondo il protocollo stabilito.

## Formato dei Dati di Scambio

### Richiesta JSON SDK (da C64-LLM / C64-GUI ──► PYC64)

```json
{
  "version": "1.0",
  "source_code": "...",
  "options": {
    "target": "c64"
  }
}
```

### Risposta JSON SDK (da PYC64 ──► C64-LLM / C64-GUI)

```json
{
  "version": "1.0",
  "status": "success | error",
  "artifacts": {
    "prg_base64": "...",
    "basic_code": "..."
  },
  "metrics": {
    "compile_time_ms": 120,
    "binary_size_bytes": 2048
  },
  "diagnostics": [
    {
      "severity": "error",
      "line": 5,
      "column": 12,
      "message": "..."
    }
  ]
}
```
