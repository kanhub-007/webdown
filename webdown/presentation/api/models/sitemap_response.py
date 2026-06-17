"""API response model for sitemap exploration."""

from pydantic import BaseModel

from webdown.presentation.api.models.sitemap_url_info import SitemapUrlInfo


class SitemapResponse(BaseModel):
    """Response model for sitemap exploration."""

    pages: list[SitemapUrlInfo]
    total_count: int
    sitemap_files_visited: list[str]
    total_available: int | None = None
    truncated: bool = False
