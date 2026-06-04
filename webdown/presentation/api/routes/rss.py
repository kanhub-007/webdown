"""
RSS aggregation endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request

from webdown.core.application.use_cases.aggregate_rss_feeds import AggregateRssFeedsUseCase
from webdown.presentation.api.models import AggregatedRssResponse
from webdown.presentation.api.presenters.rss_presenter import RssPresenter

router = APIRouter(prefix="/api/rss", tags=["RSS Aggregation"])


def get_aggregate_rss_feeds_use_case(request: Request) -> AggregateRssFeedsUseCase:
    return request.app.state.aggregate_rss_feeds_use_case


def get_rss_presenter() -> RssPresenter:
    return RssPresenter()


@router.get("/aggregate", response_model=AggregatedRssResponse)
async def get_aggregated_feeds(
    published_after: datetime | None = Query(
        None,
        description="Only return articles published on or after this time (ISO 8601 format, e.g. 2026-06-01T00:00:00Z)",
        examples=["2026-06-01T00:00:00Z"],
    ),
    use_case: AggregateRssFeedsUseCase = Depends(get_aggregate_rss_feeds_use_case),
    presenter: RssPresenter = Depends(get_rss_presenter),
):
    """Aggregate RSS feeds from multiple news sources.

    Pulls from Bloomberg, ZeroHedge, Huggingface Blog, Google AI Blog, and
    MIT Technology Review. Articles are deduplicated by URL and sorted newest
    first. Results are cached for 5 minutes when no date filter is applied.
    """
    feed_items = await use_case.execute(published_after=published_after)
    return presenter.to_response(feed_items)
