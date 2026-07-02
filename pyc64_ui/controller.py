"""Controller — pure orchestration between UI and compiler.

The UI only calls the engine and renders whatever comes back.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from pyc64c.engine import run_pipeline, hex_dump


@dataclass
class CompileResult:
    ok: bool = False
    prg: Optional[bytes] = None
    prg_size: int = 0
    basic_code: str = ''
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    listing: list = field(default_factory=list)
    labels: dict = field(default_factory=dict)
    hex_lines: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


def compile_source_text(source: str, filename: str = 'untitled') -> CompileResult:
    """Run full pyc64c pipeline via engine. Returns CompileResult."""
    engine_res = run_pipeline(source, {"generate_symbols": True})

    res = CompileResult()
    res.ok = engine_res.success
    res.prg = engine_res.prg
    res.prg_size = engine_res.metrics.get("binary_size_bytes", 0)
    res.basic_code = engine_res.basic_code
    res.listing = engine_res.listing
    res.labels = engine_res.labels
    res.metrics = engine_res.metrics

    if engine_res.prg:
        res.hex_lines = hex_dump(engine_res.prg)

    for diag in engine_res.diagnostics:
        msg = diag["message"]
        line = diag.get("line")
        col = diag.get("column")
        src = diag.get("source", "engine")

        formatted = f"{src.capitalize()} [{line if line else '?'}:{col if col else '?'}] {msg}"
        if diag["severity"] == "error":
            res.errors.append(formatted)
        else:
            res.warnings.append(formatted)

    return res


def compile_source_basic(source: str) -> str:
    """BASIC-only pipeline. Returns BASIC source string."""
    engine_res = run_pipeline(source)
    return engine_res.basic_code
