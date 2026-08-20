import hashlib
import json
import time
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from services.kb_agent.versioning import KBVersioning
from services.kb_agent.quality import QualityGate
from services.kb_agent.llm_adapter import LLMAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("services.kb_agent")

app = FastAPI(
    title="C64 Knowledge Base Agent Service",
    description="Microservice for C64 Knowledge Base management, FTS5 search, document ingestion, and versioning",
    version="1.0.0"
)

versioning_service = KBVersioning()

# Shared documents database
documents_db: List[Dict[str, Any]] = [
    {
        "id": "doc_vic_color_1",
        "source_url": "https://www.c64-wiki.com/wiki/VIC-II",
        "source_repo": "C64-KB-Agent",
        "spider_name": "c64wiki",
        "content_type": "manual",
        "language": "basic_v2",
        "content": "To change the background color in Commodore 64, write to memory location 53281 ($D021). To change border color, write to 53280 ($D020). Example: POKE 53280,2.",
        "category": "video",
        "metadata": {
            "title": "VIC-II Color Register Setup",
            "tags": ["video", "vic-ii", "colors"],
            "author": "C64-Wiki",
            "quality_score": 95.0
        },
        "validation_status": "syntax_ok",
        "validation_feedback": []
    },
    {
        "id": "doc_raster_int_2",
        "source_url": "https://codebase64.org/doku.php?id=base:raster_interrupts",
        "source_repo": "C64-KB-Agent",
        "spider_name": "codebase64",
        "content_type": "source_code",
        "language": "acme",
        "content": "Raster interrupts allow running code at specific screen lines. Register $D012 is used to set the line. $D011 (MSB) and $D019/$D01A manage raster interrupts.",
        "category": "interrupts",
        "metadata": {
            "title": "Raster Interrupts",
            "tags": ["interrupts", "raster", "6502"],
            "author": "Codebase64",
            "quality_score": 90.0
        },
        "validation_status": "syntax_ok",
        "validation_feedback": []
    }
]

quarantine_db: List[Dict[str, Any]] = []

class IngestRequest(BaseModel):
    documents: List[Dict[str, Any]]

class FeedbackRequest(BaseModel):
    error_type: str
    severity: str
    suggestion: Optional[str] = None
    context: Optional[str] = None

@app.get("/")
def read_root():
    return {"status": "running", "service": "C64 Knowledge Base Agent Service", "version": versioning_service.get_current_version()}

@app.get("/status")
def get_status():
    manifest = versioning_service.manifest
    return {
        "status": "ok",
        "documents_count": len(documents_db),
        "quarantined_count": len(quarantine_db),
        "version": versioning_service.get_current_version(),
        "dataset_hash": manifest.get("dataset_hash"),
        "last_sync": manifest.get("last_sync")
    }

@app.get("/documents")
def list_documents(
    page: int = 1,
    limit: int = 10,
    tag: Optional[str] = None,
    language: Optional[str] = None,
    content_type: Optional[str] = None
):
    filtered = []
    for doc in documents_db:
        if tag and tag not in doc.get("metadata", {}).get("tags", []):
            continue
        if language and doc.get("language") != language:
            continue
        if content_type and doc.get("content_type") != content_type:
            continue
        filtered.append(doc)

    start = (page - 1) * limit
    end = start + limit
    return {
        "page": page,
        "limit": limit,
        "total": len(filtered),
        "documents": filtered[start:end]
    }

@app.get("/documents/{doc_id}")
def get_document(doc_id: str):
    for doc in documents_db:
        if str(doc.get("id")) == str(doc_id):
            return doc
    raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

@app.post("/documents/ingest")
def ingest_documents(req: IngestRequest):
    ingested_count = 0
    quarantined_count = 0

    for raw_doc in req.documents:
        score, is_quarantined = QualityGate.evaluate_document(raw_doc)
        raw_doc.setdefault("metadata", {})["quality_score"] = score

        if is_quarantined:
            quarantine_db.append(raw_doc)
            quarantined_count += 1
        else:
            documents_db.append(raw_doc)
            ingested_count += 1

    versioning_service.manifest["documents_count"] = len(documents_db)
    versioning_service.save_manifest()

    return {
        "success": True,
        "ingested": ingested_count,
        "quarantined": quarantined_count,
        "total_documents": len(documents_db)
    }

@app.post("/documents/{doc_id}/feedback")
def submit_feedback(doc_id: str, fb: FeedbackRequest):
    target_doc = None
    for doc in documents_db:
        if str(doc.get("id")) == str(doc_id):
            target_doc = doc
            break

    if not target_doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    feedbacks = target_doc.setdefault("validation_feedback", [])
    fb_dict = fb.model_dump() if hasattr(fb, "model_dump") else fb.dict()
    feedbacks.append(fb_dict)

    # If severe validation errors exceed threshold, reject document
    severe_errors = [f for f in feedbacks if f.get("severity") in ["error", "fatal", "high"]]
    if len(severe_errors) >= 3:
        target_doc["validation_status"] = "rejected"
        logger.warning(f"Document {doc_id} marked as REJECTED due to multiple validation errors.")

    return {
        "success": True,
        "document_id": doc_id,
        "validation_status": target_doc.get("validation_status"),
        "total_feedbacks": len(feedbacks)
    }

@app.post("/index/rebuild")
def rebuild_index(bump: Optional[str] = "patch"):
    new_version = versioning_service.bump_version(bump_type=bump or "patch", release_notes="Automatic FTS5 index rebuild")
    dataset_hash = hashlib.sha256(json.dumps([d["id"] for d in documents_db]).encode('utf-8')).hexdigest()
    versioning_service.manifest["dataset_hash"] = dataset_hash
    versioning_service.save_manifest()

    LLMAdapter.notify_index_updated(new_version, dataset_hash)

    return {
        "success": True,
        "version": new_version,
        "documents_indexed": len(documents_db),
        "dataset_hash": dataset_hash
    }

@app.get("/search")
def search_kb(q: str, limit: int = 5):
    if not q:
        return {"query": q, "results": []}

    query_words = set(q.lower().split())
    results = []

    for doc in documents_db:
        score = 0.0
        content = doc.get("content", "").lower()
        title = doc.get("metadata", {}).get("title", "").lower()

        for word in query_words:
            if word in title:
                score += 2.0
            if word in content:
                score += 1.0

        if score > 0:
            quality_score = doc.get("metadata", {}).get("quality_score", 100.0)
            final_score = score * (quality_score / 100.0)
            results.append({
                "document": doc,
                "score": final_score
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return {
        "query": q,
        "results": [r["document"] for r in results[:limit]]
    }

@app.get("/releases")
def list_releases():
    return {"releases": versioning_service.list_releases()}

@app.get("/releases/{version}/download")
def download_release(version: str):
    return {
        "version": version,
        "documents_count": len(documents_db),
        "dataset": documents_db
    }

@app.get("/documents/quality-report")
def get_quality_report():
    scores = [d.get("metadata", {}).get("quality_score", 0.0) for d in documents_db]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    return {
        "total_active_documents": len(documents_db),
        "total_quarantined_documents": len(quarantine_db),
        "average_quality_score": round(avg_score, 2),
        "quarantined_items": quarantine_db
    }
