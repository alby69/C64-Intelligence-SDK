import pytest
from fastapi.testclient import TestClient
from c64_kb_agent.api import app as kb_app
from core.pipeline.acquisition.kb_client import KBAgentClient

kb_test_client = TestClient(kb_app)

def test_rag_pipeline_integration():
    # 1. Ingest document into KB Agent
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

    # 2. Query via KBAgentClient HTTP SDK
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

    # 3. Test FTS5 Search API via client SDK
    search_results = kb_sdk_client.search_kb("Sound Interface Device")
    assert len(search_results) > 0
