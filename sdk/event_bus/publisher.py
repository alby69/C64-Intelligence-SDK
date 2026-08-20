from typing import Dict, Any, Optional
from sdk.event_bus.event_bus import EventBus

class EventPublisher:
    """Convenience wrapper for publishing ecosystem events."""

    def __init__(self, sender_name: str = "Publisher", event_bus: Optional[EventBus] = None):
        self.bus = event_bus or EventBus(sender_name=sender_name)

    def publish_document_ingested(self, doc_id: str, count: int = 1):
        return self.bus.publish("kb.document.ingested", {"doc_id": doc_id, "count": count})

    def publish_index_rebuilt(self, version: str, dataset_hash: str):
        return self.bus.publish("kb.index.rebuilt", {"version": version, "dataset_hash": dataset_hash})

    def publish_spider_finished(self, spider_name: str, document_count: int):
        return self.bus.publish("scrapy.spider.finished", {"spider_name": spider_name, "document_count": document_count})
