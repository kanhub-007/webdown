"""Web search endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Request

from webdown.core.application.dto.search_web_request import SearchWebRequest
from webdown.core.application.use_cases.search_web import SearchWebUseCase
from webdown.core.domain.exceptions import SearchServiceError
from webdown.presentation.api.models.search_request import SearchRequest
from webdown.presentation.api.models.search_response import SearchResponse
from webdown.presentation.api.presenters.search_presenter import SearchPresenter

router = APIRouter(prefix="/api/search", tags=["Web Search"])


def get_search_web_use_case(request: Request) -> SearchWebUseCase:
    """Get the search web use case from application state."""
    return request.app.state.search_web_use_case


def get_search_presenter() -> SearchPresenter:
    """Get the search presenter."""
    return SearchPresenter()


@router.post("", response_model=SearchResponse)
async def search_web(
    request: SearchRequest,
    use_case: SearchWebUseCase = Depends(get_search_web_use_case),
    presenter: SearchPresenter = Depends(get_search_presenter),
):
    """Search the web for pages matching a query.

    Returns up to max_results pages with titles, URLs, and snippets.
    Use the returned URLs with the markdown conversion endpoints
    to convert discovered pages to Markdown.
    """
    try:
        dto = SearchWebRequest(query=request.query, max_results=request.max_results)
        result = use_case.execute(dto)
        return presenter.to_response(result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except SearchServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
