import os
import logging
import requests

logger = logging.getLogger("services.kb_agent.llm_adapter")

LLM_EVENT_ENDPOINT = os.environ.get("LLM_EVENT_ENDPOINT", "http://llm-core:7860/api/v1/events")

class LLMAdapter:
    """Adapter to notify C64-LLM of KB index updates via HTTP POST."""

    @staticmethod
    def notify_index_updated(version: str, dataset_hash: str, endpoint: str = None) -> bool:
        url = endpoint or LLM_EVENT_ENDPOINT
        payload = {
            "event_type": "kb.index.rebuilt",
            "version": version,
            "dataset_hash": dataset_hash,
            "sender": "C64-KB-Agent"
        }
        try:
            resp = requests.post(url, json=payload, timeout=5)
            logger.info(f"Notified LLM endpoint {url} of index rebuild (Status: {resp.status_code})")
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Could not notify LLM endpoint {url}: {e}")
            return False
