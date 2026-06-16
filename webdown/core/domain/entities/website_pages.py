"""Domain entity for discovered website pages."""

from dataclasses import dataclass, field

from webdown.core.domain.entities.sitemap_url import SitemapUrl


@dataclass
class WebsitePages:
    """Represents sitemap-discovered pages and the sitemap files visited."""

    pages: list[SitemapUrl] = field(default_factory=list)
    sitemap_files_visited: list[str] = field(default_factory=list)
    # Fidelity: how many same-site pages the sitemap declared, and whether the
    # returned list was capped by max_pages. Let callers know the inventory is
    # complete (truncated=False) or a sample (truncated=True).
    total_available: int | None = None
    truncated: bool = False
