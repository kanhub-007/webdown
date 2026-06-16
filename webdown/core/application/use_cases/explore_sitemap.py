"""Use case for exploring website sitemaps."""

from webdown.core.application.dto.sitemap_explore_request import SitemapExploreRequest
from webdown.core.application.dto.sitemap_explore_result import SitemapExploreResult
from webdown.core.domain.interfaces.sitemap_discovery_service import SitemapDiscoveryService


class ExploreSitemapUseCase:
    """Explores a website sitemap and returns discovered pages."""

    def __init__(self, sitemap_discovery_service: SitemapDiscoveryService) -> None:
        """Initialize with the sitemap discovery service."""
        self._sitemap_discovery_service = sitemap_discovery_service

    def execute(self, request: SitemapExploreRequest) -> SitemapExploreResult:
        """Discover pages from a website sitemap."""
        website_pages = self._sitemap_discovery_service.discover_website_pages(
            request.base_url,
            max_pages=request.max_pages,
        )
        return SitemapExploreResult(
            pages=list(website_pages.pages),
            sitemap_files_visited=list(website_pages.sitemap_files_visited),
            total_available=website_pages.total_available,
            truncated=website_pages.truncated,
        )
