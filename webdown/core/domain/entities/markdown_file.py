"""Domain entity for a generated markdown file."""

from dataclasses import dataclass, field

from webdown.core.domain.entities.sitemap_url import SitemapUrl


@dataclass
class MarkdownFile:
    """Represents generated markdown content and its metadata."""

    job_id: str
    content: str
    created_at: str
    ip_address: str
    file_size: int
    generation_time_seconds: float
    base_url: str
    status: str = "completed"
    sitemap_urls: list[SitemapUrl] = field(default_factory=list)
    id: int | None = None
