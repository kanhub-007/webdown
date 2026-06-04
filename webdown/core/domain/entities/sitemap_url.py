"""Domain entity for a sitemap URL entry."""

from dataclasses import dataclass


@dataclass
class SitemapUrl:
    """Represents a URL discovered from a sitemap."""

    loc: str
    lastmod: str | None = None
    changefreq: str | None = None
    priority: str | None = None
