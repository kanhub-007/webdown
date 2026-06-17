"""RSS feed aggregation service backed by feedparser and httpx."""

import calendar
import json
import logging
import re
import time
import time as _time_module
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

import feedparser
import httpx

from cachetools import TTLCache

from webdown.core.domain.entities.feed_item import FeedItem
from webdown.core.domain.interfaces.rss_feed_aggregator import RssFeedAggregator

logger = logging.getLogger(__name__)

_DEFAULT_FEEDS = [
    {"name": "Bloomberg", "url": "https://feeds.bloomberg.com/crypto/news.rss"},
    {"name": "ZeroHedge", "url": "https://cms.zerohedge.com/fullrss2.xml"},
    {"name": "Huggingface Blog", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/"},
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/"},
]


def _load_feeds() -> list[dict[str, str]]:
    """Load feed configuration from feeds.json, falling back to defaults."""
    config_path = Path(__file__).parent.parent.parent.parent / "feeds.json"
    try:
        with open(config_path, encoding="utf-8") as f:
            feeds = json.load(f)
        if isinstance(feeds, list) and all("name" in f and "url" in f for f in feeds):
            logger.info("Loaded %d feeds from %s", len(feeds), config_path)
            return feeds
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not load feeds.json (%s), using defaults", exc)
    return _DEFAULT_FEEDS


FEEDS = _load_feeds()

headers = {
    "User-Agent": "Feedly/1.0 (+http://www.feedly.com/fetcher.html; like FeedFetcher-Google)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml; q=0.9, */*; q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}
cache = TTLCache(maxsize=1, ttl=300)
# Negative cache: a short-lived TTL cache so a failing feed isn't re-fetched
# on every call. {url: expiry_timestamp}
_negative_cache: dict[str, float] = {}
_NEGATIVE_CACHE_TTL = 60  # seconds before retrying a failed feed


def _clean_html(text: str) -> str:
    """Remove HTML tags and convert to plain text."""
    if not text:
        return ""

    text = re.sub(r"<img[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<a[^>]*>(.*?)</a>", r"\1", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def _fetch_feed(url: str) -> list[dict]:
    """Fetch a single RSS feed with a short timeout."""
    async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
        raw = response.content
    parsed = feedparser.parse(raw)
    return parsed.entries


def _normalize_item(entry: dict, source: str) -> FeedItem:
    """Convert a feedparser entry into a domain feed item."""
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    published_dt = None
    if published and isinstance(published, time.struct_time):
        published_dt = datetime.fromtimestamp(calendar.timegm(published), tz=timezone.utc)

    raw_summary = entry.get("summary", entry.get("description", ""))
    clean_summary = _clean_html(raw_summary)

    return FeedItem(
        title=entry.get("title", "Untitled"),
        link=entry.get("link", ""),
        published=published_dt,
        summary=clean_summary,
        source=source,
    )


async def aggregate_all(published_after: datetime | None = None) -> list[FeedItem]:
    """Aggregate all configured feeds."""
    use_cache = published_after is None

    if use_cache and "data" in cache:
        return cache["data"]

    seen_links: set[str] = set()
    results: list[FeedItem] = []

    now = _time_module.time()

    # Purge expired negative-cache entries.
    for url in list(_negative_cache):
        if _negative_cache[url] < now:
            del _negative_cache[url]

    for feed in FEEDS:
        feed_url = feed["url"]
        if feed_url in _negative_cache:
            logger.debug("Skipping %s (in negative cache)", feed_url)
            continue
        try:
            entries = await _fetch_feed(feed_url)
            for entry in entries:
                item = _normalize_item(entry, feed["name"])
                if not item.link or item.link in seen_links:
                    continue
                if published_after is not None and (item.published is None or item.published < published_after):
                    continue
                seen_links.add(item.link)
                results.append(item)
        except Exception:
            logger.warning("Feed fetch failed for %s — caching failure for %ds", feed_url, _NEGATIVE_CACHE_TTL)
            _negative_cache[feed_url] = now + _NEGATIVE_CACHE_TTL
            continue

    results.sort(key=lambda x: x.published or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    if use_cache:
        cache["data"] = results

    return results


class FeedparserRssFeedAggregator(RssFeedAggregator):
    """RSS feed aggregator backed by feedparser and httpx."""

    async def aggregate_all(self, published_after: datetime | None = None) -> list[FeedItem]:
        """Aggregate all configured feeds."""
        return await aggregate_all(published_after=published_after)
