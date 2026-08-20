from typing import Callable, Dict, Any, Optional
from sdk.event_bus.event_bus import EventBus

class EventSubscriber:
    """Convenience wrapper for subscribing to ecosystem events."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.bus = event_bus or EventBus()

    def on_index_rebuilt(self, callback: Callable[[Dict[str, Any]], None]):
        self.bus.subscribe_local("kb.index.rebuilt", callback)

    def on_document_ingested(self, callback: Callable[[Dict[str, Any]], None]):
        self.bus.subscribe_local("kb.document.ingested", callback)

    def on_spider_finished(self, callback: Callable[[Dict[str, Any]], None]):
        self.bus.subscribe_local("scrapy.spider.finished", callback)
