# PYC64 Programmatic API Documentation

## Overview

PYC64 provides a Python API for compiling Python-like source code into Commodore 64 machine code (`.PRG`) and BASIC.

Per una visione d'insieme della strategia di sviluppo a lungo termine, consultare il [Piano di Implementazione](../IMPLEMENTATION_PLAN.md).

## Main Modules

### `pyc64c.compiler`

- `compile_source(src: str) -> CompileResult`: Performs lexing and parsing of the source code.
- `compile_to_prg(src: str) -> (bytes, CompileResult)`: Compiles the source code directly to PRG bytes.

### `pyc64c.sdk`

- `process_sdk_request(request_json: str) -> str`: Processes a JSON request according to the C64-Intelligence-SDK protocol.

## Data Formats

### SDK JSON Request

```json
{
  "version": "1.0",
  "source_code": "...",
  "options": {
    "target": "c64"
  }
}
```

### SDK JSON Response

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
