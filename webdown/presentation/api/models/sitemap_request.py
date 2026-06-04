"""API request model for sitemap exploration."""

from pydantic import BaseModel, Field, HttpUrl


class SitemapRequest(BaseModel):
    """Request model for sitemap exploration."""

    base_url: HttpUrl = Field(description="The website URL to explore (e.g., https://example.com)")
    max_pages: int | None = Field(default=1000, description="Maximum number of pages to discover (default 1000)")
