"""Application DTO for sitemap exploration request parameters."""

from dataclasses import dataclass


@dataclass
class SitemapExploreRequest:
    """Request data for exploring a website sitemap."""

    base_url: str
    max_pages: int | None = None
