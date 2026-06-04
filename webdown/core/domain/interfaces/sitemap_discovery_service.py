"""Domain service interface for sitemap discovery."""

from abc import ABC, abstractmethod

from webdown.core.domain.entities.website_pages import WebsitePages


class SitemapDiscoveryService(ABC):
    """Discovers pages from website sitemaps."""

    @abstractmethod
    def discover_website_pages(self, base_url: str, max_pages: int | None = None) -> WebsitePages:
        """Discover website pages from sitemap files."""
