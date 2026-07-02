import json
import base64
import time
from .compiler import compile_to_prg, analyze_ast

def process_sdk_request(request_json):
    """
    Process a JSON request following the C64-Intelligence-SDK protocol.

    Request format:
    {
      "version": "1.0",
      "source_code": "...",
      "options": {
        "target": "c64",
        "generate_symbols": bool
      }
    }
    """
    try:
        req = json.loads(request_json)
    except json.JSONDecodeError as e:
        return json.dumps({
            "status": "error",
            "diagnostics": [{"severity": "error", "message": f"Invalid JSON: {str(e)}"}]
        })

    source = req.get("source_code", "")
    options = req.get("options", {})

    start_time = time.time()
    prg_data, result = compile_to_prg(source)
    end_time = time.time()

    response = {
        "version": "1.0",
        "status": "success" if result.success and not result.lex_errors and not result.parse_errors else "error",
        "artifacts": {},
        "metrics": {
            "compile_time_ms": int((end_time - start_time) * 1000)
        },
        "diagnostics": []
    }

    if result.lex_errors:
        for e in result.lex_errors:
            response["diagnostics"].append({
                "severity": "error",
                "line": e.get("line"),
                "column": e.get("col"),
                "message": e.get("msg")
            })

    if result.parse_errors:
        for e in result.parse_errors:
            response["diagnostics"].append({
                "severity": "error",
                "line": e.get("line"),
                "column": e.get("col"),
                "message": e.get("msg")
            })

    if prg_data:
        response["artifacts"]["prg_base64"] = base64.b64encode(prg_data).decode('ascii')
        response["artifacts"]["basic_code"] = result.basic_code
        if options.get("generate_symbols"):
            response["artifacts"]["symbols"] = result.builder.e.generate_symbols()
        response["metrics"]["binary_size_bytes"] = len(prg_data)

        # Analyze AST for more metrics
        if result.ast:
            stats = analyze_ast(result.ast)
            response["metrics"]["global_vars"] = stats.get("globalVars")
            response["metrics"]["func_count"] = stats.get("funcCount")

    return json.dumps(response, indent=2)
