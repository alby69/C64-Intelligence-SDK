import os
import sys
import logging

# Ensure kb-agent submodule is in sys.path
kb_agent_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "kb-agent"))
if kb_agent_root not in sys.path:
    sys.path.insert(0, kb_agent_root)

from c64_kb_agent.api import app, documents_db

__all__ = ["app", "documents_db"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
