"""Domain service interface for RSS feed aggregation."""

from abc import ABC, abstractmethod
from datetime import datetime

from webdown.core.domain.entities.feed_item import FeedItem


class RssFeedAggregator(ABC):
    """Aggregates RSS and Atom feed items."""

    @abstractmethod
    async def aggregate_all(self, published_after: datetime | None = None) -> list[FeedItem]:
        """Aggregate all configured feeds."""
