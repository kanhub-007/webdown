"""Domain entity for an RSS feed item."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class FeedItem:
    """Represents one normalized feed item from an RSS or Atom feed."""

    title: str
    link: str
    source: str
    published: datetime | None = None
    summary: str | None = None
