"""API response model for aggregated RSS feeds."""

from datetime import datetime

from pydantic import BaseModel

from webdown.presentation.api.models.rss_feed_item import RssFeedItem


class AggregatedRssResponse(BaseModel):
    """Response model for aggregated RSS feeds."""

    items: list[RssFeedItem]
    total: int
    generated_at: datetime
