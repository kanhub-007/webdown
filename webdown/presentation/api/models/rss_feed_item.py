"""API model for a single RSS feed item."""

from datetime import datetime

from pydantic import BaseModel


class RssFeedItem(BaseModel):
    """Model for a single RSS feed item."""

    title: str
    link: str
    published: datetime | None = None
    summary: str | None = None
    source: str
