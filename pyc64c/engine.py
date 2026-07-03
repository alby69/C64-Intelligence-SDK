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
from .simulation_engine import C64Simulator

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
    simulation_output: str = ""
    simulation_history: List[Dict[str, Any]] = field(default_factory=list)

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

        if options.get("simulate"):
            sim = C64Simulator(res.prg, symbols=res.labels)
            max_steps = options.get("sim_max_steps", 1000)
            sim.run(max_steps=max_steps)
            res.simulation_output = sim.output_buffer
            res.simulation_history = sim.history

    # AI self-healing suggestions
    if not res.success:
        new_diagnostics = []
        for diag in res.diagnostics:
            if diag.get("severity") == "error":
                msg = diag.get("message", "").lower()
                if "undefined" in msg:
                    import re
                    # Look for things like 'variable name' or "variable name" or just variable name at end
                    match = re.search(r"['\"]?([a-zA-Z0-9_]+)['\"]?\s*$", diag["message"])
                    var_name = match.group(1) if match else "variable"
                    new_diagnostics.append({
                        "severity": "info",
                        "source": "ai-assistant",
                        "message": f"AI Suggestion: The variable '{var_name}' is used but not defined. Check spelling or add 'var {var_name}: byte = 0'."
                    })
                elif "type mismatch" in msg:
                    new_diagnostics.append({
                        "severity": "info",
                        "source": "ai-assistant",
                        "message": "AI Suggestion: Type mismatch detected. Ensure you are not assigning a 16-bit value to an 8-bit variable without a cast."
                    })
                elif "syntax error" in msg:
                    new_diagnostics.append({
                        "severity": "info",
                        "source": "ai-assistant",
                        "message": "AI Suggestion: Syntax error. Remember that PYC64 requires explicit type annotations for variables and function returns."
                    })
        res.diagnostics.extend(new_diagnostics)

    return res
