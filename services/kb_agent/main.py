import uvicorn
from services.kb_agent.api import app, documents_db

__all__ = ["app", "documents_db"]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
