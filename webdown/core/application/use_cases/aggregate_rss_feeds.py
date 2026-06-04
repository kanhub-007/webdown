"""Use case for aggregating RSS feeds."""

from datetime import datetime

from webdown.core.domain.entities.feed_item import FeedItem
from webdown.core.domain.interfaces.rss_feed_aggregator import RssFeedAggregator


class AggregateRssFeedsUseCase:
    """Aggregates configured RSS feeds."""

    def __init__(self, rss_feed_aggregator: RssFeedAggregator) -> None:
        """Initialize with the RSS feed aggregator."""
        self._rss_feed_aggregator = rss_feed_aggregator

    async def execute(self, published_after: datetime | None = None) -> list[FeedItem]:
        """Aggregate configured RSS feeds."""
        return await self._rss_feed_aggregator.aggregate_all(published_after=published_after)
