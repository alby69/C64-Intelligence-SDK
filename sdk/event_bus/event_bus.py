import time
import uuid
import logging
import requests
from typing import Dict, Any, List, Callable, Optional
from c64_schemas import validate_event

logger = logging.getLogger("sdk.event_bus")

class EventBus:
    """Lightweight Redis-less HTTP/In-Memory Event Bus for C64 Ecosystem."""

    def __init__(self, sender_name: str = "C64EcosystemService"):
        self.sender_name = sender_name
        self.local_subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self.remote_subscribers: Dict[str, List[str]] = {}

    def subscribe_local(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe local in-memory callback to an event type."""
        self.local_subscribers.setdefault(event_type, []).append(callback)

    def subscribe_remote(self, event_type: str, callback_url: str):
        """Register HTTP callback URL for an event type."""
        self.remote_subscribers.setdefault(event_type, []).append(callback_url)

    def publish(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Publish an event to local and remote subscribers."""
        event_data = {
            "event_type": event_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sender": self.sender_name,
            "payload": payload
        }

        # Validate event schema
        try:
            validate_event(event_data)
        except Exception as e:
            logger.warning(f"Event schema validation warning: {e}")

        # Notify local subscribers
        if event_type in self.local_subscribers:
            for cb in self.local_subscribers[event_type]:
                try:
                    cb(event_data)
                except Exception as e:
                    logger.error(f"Local subscriber error: {e}")

        # Notify remote subscribers
        if event_type in self.remote_subscribers:
            for url in self.remote_subscribers[event_type]:
                try:
                    requests.post(url, json=event_data, timeout=3)
                except Exception as e:
                    logger.error(f"Remote subscriber POST error for {url}: {e}")

        return event_data
