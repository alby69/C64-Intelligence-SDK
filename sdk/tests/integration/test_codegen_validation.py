import pytest
from fastapi.testclient import TestClient
from c64_kb_agent.api import app as kb_app
from core.agent.validator import ValidatorAgent, ValidationReporter
from core.utils.sandbox import Py6502Sandbox

kb_test_client = TestClient(kb_app)

def test_codegen_validation_and_feedback_loop():
    # 1. Ingest a document that will receive feedback (score >= 60 to pass Quality Gate)
    doc_payload = {
        "id": "code_feedback_doc_1",
        "source_url": "https://codebase64.org/test_code",
        "source_repo": "C64-Scrapy",
        "spider_name": "codebase64",
        "content_type": "source_code",
        "language": "acme",
        "content": "# Complete Assembly Routine for C64 Background Color Setup\nLDA #$00\nSTA $D020\nSTA $D021\nRTS",
        "metadata": {"title": "Sample Assembly Code", "tags": ["assembly", "c64"], "quality_score": 85.0},
        "validation_status": "syntax_ok"
    }

    ingest_res = kb_test_client.post("/documents/ingest", json={"documents": [doc_payload]})
    assert ingest_res.status_code == 200
    assert ingest_res.json()["ingested"] == 1

    # 2. Test Sandboxed Execution
    sandbox = Py6502Sandbox(default_timeout_seconds=2.0)
    exec_res = sandbox.execute_code(lambda x: x + 10, (5,))
    assert exec_res["success"] is True
    assert exec_res["result"] == 15

    # 3. Test Validator Agent reporting feedback
    def mock_post(url, json=None, timeout=5):
        path = url.replace("http://kb-agent:8002", "")
        return kb_test_client.post(path, json=json)

    import requests
    requests.post = mock_post

    validator = ValidatorAgent()
    # Test BASIC code with non-sequential line numbers to trigger linter failure
    invalid_basic = "```basic\n20 PRINT \"WORLD\"\n10 PRINT \"HELLO\"\n```"
    success, log = validator.validate(invalid_basic, doc_id="code_feedback_doc_1")
    assert success is False

    # Check feedback was recorded on document
    doc_resp = kb_test_client.get("/documents/code_feedback_doc_1")
    assert doc_resp.status_code == 200
    doc_data = doc_resp.json()
    assert len(doc_data.get("validation_feedback", [])) > 0
