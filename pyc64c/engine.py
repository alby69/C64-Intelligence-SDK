"""Engine — Core orchestration for PYC64.

This module provides a unified interface for compiling source code,
generating artifacts, and collecting metrics/diagnostics.
It is used by both the TUI and the SDK/API layers.
"""

import time
import base64
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from .compiler import compile_to_prg, analyze_ast

@dataclass
class EngineResult:
    success: bool = False
    prg: Optional[bytes] = None
    basic_code: str = ''
    listing: List[str] = field(default_factory=list)
    labels: Dict[str, int] = field(default_factory=dict)
    symbols: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    diagnostics: List[Dict[str, Any]] = field(default_factory=list)

def hex_dump(data: bytes, addr: int = 0x0801, width: int = 16) -> List[tuple]:
    """Return list of (offset, hex_str, ascii_str) tuples."""
    lines = []
    for i in range(0, len(data), width):
        chunk = data[i:i + width]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append((addr + i, hex_str, ascii_str))
    return lines

def run_pipeline(source: str, options: Optional[Dict[str, Any]] = None) -> EngineResult:
    """Run the full PYC64 pipeline and return a structured EngineResult."""
    if options is None:
        options = {}

    res = EngineResult()
    start_time = time.time()

    prg_data, result = compile_to_prg(source)
    end_time = time.time()

    res.metrics["compile_time_ms"] = int((end_time - start_time) * 1000)

    # Collect diagnostics
    if result.lex_errors:
        for e in result.lex_errors:
            res.diagnostics.append({
                "severity": "error",
                "source": "lexer",
                "line": e.get("line"),
                "column": e.get("col"),
                "message": e.get("msg")
            })

    if result.parse_errors:
        for e in result.parse_errors:
            res.diagnostics.append({
                "severity": "error",
                "source": "parser",
                "line": e.get("line"),
                "column": e.get("col"),
                "message": e.get("msg")
            })

    if prg_data is None:
        if result.builder and result.builder.fixup_errs:
            for e in result.builder.fixup_errs:
                res.diagnostics.append({
                    "severity": "error",
                    "source": "fixup",
                    "message": str(e)
                })
        elif not res.diagnostics:
            res.diagnostics.append({
                "severity": "error",
                "source": "engine",
                "message": "Compilation failed: no PRG produced"
            })
    else:
        res.success = True
        res.prg = prg_data
        res.basic_code = getattr(result, 'basic_code', '')
        res.metrics["binary_size_bytes"] = len(prg_data)

        builder = getattr(result, 'builder', None)
        if builder:
            res.listing = getattr(builder.e, 'listing', [])
            res.labels = getattr(builder.e, 'labels', {})
            if options.get("generate_symbols"):
                res.symbols = builder.e.generate_symbols()

        if result.ast:
            stats = analyze_ast(result.ast)
            res.metrics.update(stats)

    # AI self-healing suggestions
    if not res.success:
        new_diagnostics = []
        for diag in res.diagnostics:
            if diag["severity"] == "error":
                if "undefined" in diag["message"].lower():
                    new_diagnostics.append({
                        "severity": "info",
                        "source": "ai-assistant",
                        "message": f"Suggestion: Ensure variable '{diag['message'].split()[-1]}' is declared before use."
                    })
        res.diagnostics.extend(new_diagnostics)

    return res
