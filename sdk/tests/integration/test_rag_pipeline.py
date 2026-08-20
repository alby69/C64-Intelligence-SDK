import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent.parent
for p in [str(root_dir), str(root_dir / "services"), str(root_dir / "core"), str(root_dir / "sdk" / "schemas")]:
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest
from fastapi.testclient import TestClient
from services.kb_agent.api import app as kb_app
from core.pipeline.acquisition.kb_client import KBAgentClient

kb_test_client = TestClient(kb_app)

def test_rag_pipeline_integration():
    doc_payload = {
        "id": "rag_test_doc_1",
        "source_url": "https://www.c64-wiki.com/wiki/SID",
        "source_repo": "C64-Scrapy",
        "spider_name": "c64wiki",
        "content_type": "manual",
        "language": "basic_v2",
        "content": "The Sound Interface Device (SID) chip is at address $D400 (54272). Voice 1 frequency low byte is $D400, high byte is $D401.",
        "category": "audio",
        "metadata": {
            "title": "SID Sound Chip Basics",
            "tags": ["sid", "sound", "audio"],
            "quality_score": 90.0
        },
        "validation_status": "syntax_ok"
    }

    resp = kb_test_client.post("/documents/ingest", json={"documents": [doc_payload]})
    assert resp.status_code == 200

    kb_sdk_client = KBAgentClient(base_url="http://testserver")

    def mock_get(url, params=None, timeout=5):
        path = url.replace("http://testserver", "")
        return kb_test_client.get(path, params=params)

    import requests
    requests.get = mock_get

    docs = kb_sdk_client.get_documents_stream()
    assert len(docs) > 0
    found = any(d.get("id") == "rag_test_doc_1" for d in docs)
    assert found

    search_results = kb_sdk_client.search_kb("Sound Interface Device")
    assert len(search_results) > 0
