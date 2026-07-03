# SDK Integration Guide

PYC64 is designed to be a decoupled and integrable component within the **C64-Intelligence-SDK**. This document explains how the integration works and how to use PYC64 as a service for other agents (like C64-LLM).

## Architecture

The integration is managed by the `IntegrationBridge` class in `pyc64c/integration.py`. This bridge handles:
1. **SDK Root Discovery**: Locating the main SDK directory to access shared resources.
2. **Shared Packages**: Dynamically importing shared Python packages from `packages/` (e.g., `c64validator`).
3. **Tutorial Access**: Fetching example code from `C64GameTutorial`.
4. **Feedback Loop**: Sending compilation results and diagnostics back to the AI Orchestrator.

## Configuration

The integration can be configured via environment variables:

- `C64_SDK_ROOT`: Path to the root of the C64-Intelligence-SDK.
- `C64_FEEDBACK_DIR`: Directory where feedback JSON files are written (default: `/tmp/c64_feedback`).

## SDK Protocol

PYC64 implements a JSON-based protocol for communication with the SDK Hub and C64-LLM. The entry point is `pyc64c.sdk.process_sdk_request`.

### Request Format

```json
{
  "source_code": "def main():\n    text_color(1)\n    print('hello')",
  "options": {
    "generate_symbols": true,
    "simulate": true
  },
  "context": {
    "session_id": "unique-session-123",
    "validate": true
  }
}
```

### Response Format

```json
{
  "version": "1.0",
  "status": "success",
  "artifacts": {
    "prg_base64": "...",
    "basic_code": "10 SYS 2061",
    "symbols": "...",
    "simulation_output": "HELLO"
  },
  "metrics": {
    "compile_time_ms": 45,
    "binary_size_bytes": 120
  },
  "diagnostics": []
}
```

## AI Self-Healing

The `Engine` in `pyc64c/engine.py` generates specific suggestions for the AI when errors occur. These are returned in the `diagnostics` array with `source: "ai-assistant"`.

Example suggestion:
```json
{
  "severity": "info",
  "source": "ai-assistant",
  "message": "AI Suggestion: The variable 'score' is used but not defined. Check spelling or add 'var score: byte = 0'."
}
```

## Using the Bridge Programmatically

```python
from pyc64c.integration import get_bridge

bridge = get_bridge()

# Check for shared validator
validator = bridge.get_validator()
if validator:
    print("SDK Validator found!")

# Get examples from tutorial
examples = bridge.get_tutorial_examples()
```
