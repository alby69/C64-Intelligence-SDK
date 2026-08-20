import pytest
from fastapi.testclient import TestClient
from c64_scraper.api import app as scrapy_app
from c64_kb_agent.api import app as kb_app

scrapy_client = TestClient(scrapy_app)
kb_client = TestClient(kb_app)

def test_acquisition_pipeline_e2e():
    # 1. Trigger spider run on Scrapy API
    run_resp = scrapy_client.post("/spiders/c64wiki/run")
    assert run_resp.status_code == 200
    job_data = run_resp.json()
    job_id = job_data["job_id"]
    assert job_data["status"] in ["pending", "running", "completed"]

    # 2. Check job status
    status_resp = scrapy_client.get(f"/jobs/{job_id}/status")
    assert status_resp.status_code == 200

    # 3. Direct document ingestion test into KB Agent
    sample_docs = [
        {
            "id": "test_e2e_doc_1",
            "source_url": "https://www.c64-wiki.com/wiki/CIA",
            "source_repo": "C64-Scrapy",
            "spider_name": "c64wiki",
            "content_type": "manual",
            "language": "markdown",
            "content": "# Complex Interface Adapter (CIA)\n\nDetailed hardware documentation for CIA 1 ($DC00) and CIA 2 ($DD00).",
            "metadata": {
                "title": "CIA Hardware Overview",
                "tags": ["cia", "hardware", "c64"]
            },
            "validation_status": "syntax_ok"
        }
    ]

    ingest_resp = kb_client.post("/documents/ingest", json={"documents": sample_docs})
    assert ingest_resp.status_code == 200
    assert ingest_resp.json()["ingested"] == 1

    # 4. Search and retrieve via KB Agent API
    search_resp = kb_client.get("/search?q=CIA")
    assert search_resp.status_code == 200
    results = search_resp.json()["results"]
    assert len(results) > 0
    assert results[0]["id"] == "test_e2e_doc_1"
