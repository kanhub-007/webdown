"""Presenter for web search endpoints."""

from webdown.core.application.dto.search_web_response import SearchWebResponse
from webdown.presentation.api.models.search_response import SearchResponse, SearchResultItem


class SearchPresenter:
    """Converts search DTOs to Pydantic API response models."""

    def to_response(self, result: SearchWebResponse) -> SearchResponse:
        """Convert a search response DTO to the Pydantic response model."""
        return SearchResponse(
            query=result.query,
            results=[
                SearchResultItem(title=item.title, url=item.url, snippet=item.snippet)
                for item in result.items
            ],
            total_count=len(result.items),
        )
