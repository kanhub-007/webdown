"""API response model for generated markdown file metadata."""

from pydantic import BaseModel

from webdown.presentation.api.models.sitemap_url_info import SitemapUrlInfo


class MarkdownFileMetadata(BaseModel):
    """Response model for markdown file metadata."""

    job_id: str
    created_at: str
    ip_address: str
    file_size: int
    generation_time_seconds: float
    base_url: str
    sitemap_url_count: int
    sitemap_urls: list[SitemapUrlInfo]
