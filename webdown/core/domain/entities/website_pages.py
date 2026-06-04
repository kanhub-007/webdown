"""Domain entity for discovered website pages."""

from dataclasses import dataclass, field

from webdown.core.domain.entities.sitemap_url import SitemapUrl


@dataclass
class WebsitePages:
    """Represents sitemap-discovered pages and the sitemap files visited."""

    pages: list[SitemapUrl] = field(default_factory=list)
    sitemap_files_visited: list[str] = field(default_factory=list)
