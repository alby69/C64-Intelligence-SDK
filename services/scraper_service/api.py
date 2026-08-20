import uuid
import hashlib
import time
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from services.scraper_service.webhook import send_ingestion_webhook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("c64_scrapy_api")

app = FastAPI(
    title="C64 Scrapy Service API",
    description="REST API for triggering spiders and managing scraping jobs in C64-Scrapy",
    version="1.0.0"
)

# In-memory storage for scraping jobs and results
jobs_db: Dict[str, Dict[str, Any]] = {}

class ScrapeUrlRequest(BaseModel):
    url: str
    spider_name: Optional[str] = "generic"

class JobStatusResponse(BaseModel):
    job_id: str
    spider_name: str
    status: str
    created_at: float
    completed_at: Optional[float] = None
    document_count: int = 0
    error: Optional[str] = None

class JobResultsResponse(BaseModel):
    job_id: str
    documents: List[Dict[str, Any]]

def _execute_spider_job(job_id: str, spider_name: str, target_url: Optional[str] = None):
    """Worker task simulating or running spider execution."""
    logger.info(f"Starting spider job {job_id} for spider '{spider_name}'")
    job = jobs_db.get(job_id)
    if not job:
        return

    job["status"] = "running"
    try:
        time.sleep(0.1)
        doc_id = hashlib.sha256(f"{target_url or spider_name}_{time.time()}".encode('utf-8')).hexdigest()

        url = target_url or f"https://www.c64-wiki.com/wiki/{spider_name}"
        sample_doc = {
            "id": doc_id,
            "source_url": url,
            "source_repo": "C64-Scrapy",
            "spider_name": spider_name,
            "content_type": "scraped",
            "language": "markdown",
            "content": f"# Scraped Content from {url}\n\nAutomated documentation payload for C64 architecture and 6502 programming.",
            "metadata": {
                "title": f"C64 Scraped Doc ({spider_name})",
                "tags": ["c64", spider_name, "scraped"],
                "author": "C64-Scrapy",
                "date_crawled": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "validation_status": "syntax_ok"
        }

        job["results"].append(sample_doc)
        job["status"] = "completed"
        job["completed_at"] = time.time()
        job["document_count"] = len(job["results"])

        # Notify C64-KB-Agent via webhook
        send_ingestion_webhook(job["results"])

    except Exception as e:
        logger.error(f"Error during job {job_id}: {e}")
        job["status"] = "failed"
        job["error"] = str(e)
        job["completed_at"] = time.time()

@app.get("/")
def read_root():
    return {"status": "running", "service": "C64 Scrapy Service API", "version": "1.0.0"}

@app.post("/spiders/{spider_name}/run", response_model=JobStatusResponse)
def run_spider(spider_name: str, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "spider_name": spider_name,
        "status": "pending",
        "created_at": time.time(),
        "completed_at": None,
        "document_count": 0,
        "results": [],
        "error": None
    }
    jobs_db[job_id] = job
    background_tasks.add_task(_execute_spider_job, job_id, spider_name)
    return JobStatusResponse(**job)

@app.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs_db[job_id]
    return JobStatusResponse(
        job_id=job["job_id"],
        spider_name=job["spider_name"],
        status=job["status"],
        created_at=job["created_at"],
        completed_at=job["completed_at"],
        document_count=job["document_count"],
        error=job["error"]
    )

@app.get("/jobs/{job_id}/results", response_model=JobResultsResponse)
def get_job_results(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs_db[job_id]
    return JobResultsResponse(
        job_id=job_id,
        documents=job["results"]
    )

@app.post("/spiders/scrape-url", response_model=JobStatusResponse)
def scrape_url(req: ScrapeUrlRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    spider_name = req.spider_name or "generic"
    job = {
        "job_id": job_id,
        "spider_name": spider_name,
        "status": "pending",
        "created_at": time.time(),
        "completed_at": None,
        "document_count": 0,
        "results": [],
        "error": None
    }
    jobs_db[job_id] = job
    background_tasks.add_task(_execute_spider_job, job_id, spider_name, req.url)
    return JobStatusResponse(**job)
