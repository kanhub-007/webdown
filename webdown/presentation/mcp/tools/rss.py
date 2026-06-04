"""MCP tools — RSS feed aggregation."""

import re
from datetime import datetime, timedelta, timezone

from webdown.startup.use_case_factory import create_aggregate_rss_feeds_use_case


def _parse_timeframe(value: str | None) -> datetime | None:
    """Parse a timeframe string into a UTC datetime.

    Accepts ISO 8601 datetimes or relative shortcuts:
        "24h" / "1d"  -> 24 hours ago
        "7d" / "1w"   -> 7 days ago
        "30d" / "1m"  -> 30 days ago
        "1h"          -> 1 hour ago
        None           -> no filter (return all)
    """
    if not value:
        return None
    value = value.strip()
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass
    match = re.match(r"^(\d+)\s*(h|d|w|m)$", value.lower())
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        if unit == "h":
            delta = timedelta(hours=num)
        elif unit == "d":
            delta = timedelta(days=num)
        elif unit == "w":
            delta = timedelta(weeks=num)
        elif unit == "m":
            delta = timedelta(days=num * 30)
        else:
            return None
        return datetime.now(timezone.utc) - delta
    return None


def register_rss_tools(server: object) -> None:
    """Register RSS aggregation tools on the MCP server."""

    @server.tool(
        description=(
            "Aggregate RSS feeds from cryptocurrency and AI news sources. "
            "Sources are configured in feeds.json at the project root. "
            "Returns deduplicated articles sorted newest-first with 5-minute caching. "
            "Use published_after to filter by time: ISO 8601 datetime (2026-06-01T00:00:00Z) "
            "or relative shortcuts: 24h, 7d, 1w, 30d, 1m."
        ),
    )
    async def aggregate_rss_feeds(published_after: str | None = None) -> dict:
        """Aggregate RSS feeds."""
        use_case = create_aggregate_rss_feeds_use_case()
        after = _parse_timeframe(published_after)
        items = await use_case.execute(published_after=after)
        return {
            "items": [
                {
                    "title": item.title,
                    "link": item.link,
                    "published": item.published.isoformat() if item.published else None,
                    "summary": item.summary,
                    "source": item.source,
                }
                for item in items
            ],
            "total": len(items),
        }
