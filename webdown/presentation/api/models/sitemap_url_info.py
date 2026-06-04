"""API model for a single sitemap URL entry."""

from pydantic import BaseModel


class SitemapUrlInfo(BaseModel):
    """Model for a single sitemap URL entry."""

    loc: str
    lastmod: str | None = None
