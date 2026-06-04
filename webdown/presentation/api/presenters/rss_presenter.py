"""Presenter for RSS-related endpoints."""

from datetime import datetime, timezone

from webdown.core.domain.entities.feed_item import FeedItem
from webdown.presentation.api.models import AggregatedRssResponse, RssFeedItem


class RssPresenter:
    """Converts RSS feed DTOs to Pydantic API response models."""

    def to_response(self, items: list[FeedItem]) -> AggregatedRssResponse:
        """Convert a list of feed items to the Pydantic response model."""
        api_items = [
            RssFeedItem(
                title=item.title,
                link=item.link,
                published=item.published,
                summary=item.summary,
                source=item.source,
            )
            for item in items
        ]
        return AggregatedRssResponse(
            items=api_items,
            total=len(api_items),
            generated_at=datetime.now(timezone.utc),
        )
