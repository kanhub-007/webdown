"""Pydantic model for web search response."""

from pydantic import BaseModel

from webdown.presentation.api.models.search_result_item import SearchResultItem


class SearchResponse(BaseModel):
    """Response model for web search."""

    query: str
    results: list[SearchResultItem]
    total_count: int
