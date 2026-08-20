import os
import logging
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger("scraper_service.webhook")

SCRAPY_WEBHOOK_URL = os.environ.get("SCRAPY_WEBHOOK_URL", "http://kb-agent:8002/documents/ingest")

def send_ingestion_webhook(documents: List[Dict[str, Any]], webhook_url: Optional[str] = None) -> bool:
    """
    Sends scraped documents to C64-KB-Agent webhook URL.
    Decoupled physical HTTP POST dispatch.
    """
    target_url = webhook_url or SCRAPY_WEBHOOK_URL
    if not target_url:
        logger.warning("No SCRAPY_WEBHOOK_URL configured. Skipping webhook notify.")
        return False

    try:
        payload = {"documents": documents}
        response = requests.post(target_url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info(f"Successfully notified webhook {target_url} with {len(documents)} documents.")
            return True
        else:
            logger.error(f"Webhook {target_url} returned status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to post webhook to {target_url}: {e}")
        return False
