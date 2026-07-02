import json
import base64
from .engine import run_pipeline

def process_sdk_request(request_json):
    """
    Process a JSON request following the C64-Intelligence-SDK protocol.
    Uses the central engine for processing.
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

    engine_res = run_pipeline(source, options)

    response = {
        "version": "1.0",
        "status": "success" if engine_res.success else "error",
        "artifacts": {},
        "metrics": engine_res.metrics,
        "diagnostics": engine_res.diagnostics
    }

    if engine_res.prg:
        response["artifacts"]["prg_base64"] = base64.b64encode(engine_res.prg).decode('ascii')
        response["artifacts"]["basic_code"] = engine_res.basic_code
        if engine_res.symbols:
            response["artifacts"]["symbols"] = engine_res.symbols

    return json.dumps(response, indent=2)
