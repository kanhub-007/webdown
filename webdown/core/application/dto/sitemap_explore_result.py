"""Application DTO for sitemap exploration result."""

from dataclasses import dataclass, field

from webdown.core.domain.entities.sitemap_url import SitemapUrl


@dataclass
class SitemapExploreResult:
    """Result returned after sitemap exploration."""

    pages: list[SitemapUrl] = field(default_factory=list)
    sitemap_files_visited: list[str] = field(default_factory=list)
