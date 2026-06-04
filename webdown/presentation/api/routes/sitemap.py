"""
Sitemap exploration endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request

from webdown.core.application.dto.sitemap_explore_request import SitemapExploreRequest
from webdown.core.application.use_cases.explore_sitemap import ExploreSitemapUseCase
from webdown.presentation.api.models import SitemapRequest, SitemapResponse
from webdown.presentation.api.presenters.sitemap_presenter import SitemapPresenter

router = APIRouter(prefix="/api/sitemap", tags=["Sitemap Exploration"])


def get_explore_sitemap_use_case(request: Request) -> ExploreSitemapUseCase:
    return request.app.state.explore_sitemap_use_case


def get_sitemap_presenter() -> SitemapPresenter:
    return SitemapPresenter()


@router.post("/explore", response_model=SitemapResponse)
async def explore_sitemap(
    request: SitemapRequest,
    use_case: ExploreSitemapUseCase = Depends(get_explore_sitemap_use_case),
    presenter: SitemapPresenter = Depends(get_sitemap_presenter),
):
    """Discover all pages from a website's sitemap.

    Parses sitemap.xml, sitemap index files, and robots.txt to find every page.
    Returns URLs with metadata (lastmod, changefreq, priority) and the sitemap files visited.
    Use this before converting pages to see what content is available.
    """
    try:
        dto = SitemapExploreRequest(base_url=str(request.base_url), max_pages=request.max_pages)
        result = use_case.execute(dto)
        return presenter.to_response(result)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to explore sitemap: {str(error)}")
