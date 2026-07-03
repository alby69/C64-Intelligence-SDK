import json
import base64
from .engine import run_pipeline
from .integration import get_bridge

def process_sdk_request(request_json):
    """
    Process a JSON request following the C64-Intelligence-SDK protocol.
    Uses the central engine for processing and notifies the integration bridge.
    """
    try:
        if isinstance(request_json, dict):
            req = request_json
        else:
            req = json.loads(request_json)
    except json.JSONDecodeError as e:
        return json.dumps({
            "status": "error",
            "diagnostics": [{"severity": "error", "message": f"Invalid JSON: {str(e)}"}]
        })

    source = req.get("source_code", "")
    options = req.get("options", {})
    context = req.get("context", {})
    session_id = context.get("session_id")

    # Add simulation options if requested by SDK
    if options.get("simulate") is None and context.get("validate"):
        options["simulate"] = True

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
        if engine_res.simulation_output:
             response["artifacts"]["simulation_output"] = engine_res.simulation_output

    # Notify bridge for feedback loop if integrated
    bridge = get_bridge()
    bridge.notify_llm_of_result(engine_res, session_id=session_id)

    # If we have a validator in the SDK, we could run additional checks here
    # but the engine already has a built-in simulator.

    return json.dumps(response, indent=2)
