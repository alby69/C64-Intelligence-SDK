import uuid
import time
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("sdk.telemetry")

class TraceContext:
    """Propagates trace_id across inter-service REST calls."""

    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid.uuid4())

    def to_headers(self) -> Dict[str, str]:
        return {"X-Trace-ID": self.trace_id}

    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> "TraceContext":
        trace_id = headers.get("X-Trace-ID") or headers.get("x-trace-id")
        return cls(trace_id=trace_id)

def log_event(service: str, event: str, trace_id: str, payload: Optional[Dict[str, Any]] = None):
    """Outputs structured JSON telemetry log event."""
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "service": service,
        "event": event,
        "trace_id": trace_id,
        "payload": payload or {}
    }
    logger.info(json.dumps(log_entry))
    return log_entry
