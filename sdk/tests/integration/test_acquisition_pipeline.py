import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent.parent
for p in [str(root_dir), str(root_dir / "services"), str(root_dir / "sdk" / "schemas")]:
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest
from fastapi.testclient import TestClient
from services.scraper_service.api import app as scrapy_app
from services.kb_agent.api import app as kb_app

scrapy_client = TestClient(scrapy_app)
kb_client = TestClient(kb_app)

def test_acquisition_pipeline_e2e():
    run_resp = scrapy_client.post("/spiders/c64wiki/run")
    assert run_resp.status_code == 200
    job_data = run_resp.json()
    job_id = job_data["job_id"]
    assert job_data["status"] in ["pending", "running", "completed"]

    status_resp = scrapy_client.get(f"/jobs/{job_id}/status")
    assert status_resp.status_code == 200

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

    search_resp = kb_client.get("/search?q=CIA")
    assert search_resp.status_code == 200
    results = search_resp.json()["results"]
    assert len(results) > 0
    assert results[0]["id"] == "test_e2e_doc_1"
