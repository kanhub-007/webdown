"""Presenter for sitemap-related endpoints."""

from webdown.core.application.dto.sitemap_explore_result import SitemapExploreResult
from webdown.presentation.api.models import SitemapResponse, SitemapUrlInfo


class SitemapPresenter:
    """Converts sitemap DTOs to Pydantic API response models."""

    def to_response(self, result: SitemapExploreResult) -> SitemapResponse:
        """Convert a sitemap exploration result to the Pydantic response model."""
        return SitemapResponse(
            pages=[SitemapUrlInfo(loc=page.loc, lastmod=page.lastmod) for page in result.pages],
            total_count=len(result.pages),
            sitemap_files_visited=result.sitemap_files_visited,
        )
