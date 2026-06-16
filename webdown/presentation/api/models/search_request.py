"""Pydantic model for web search request."""

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request model for web search."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    max_results: int = Field(default=20, ge=1, le=50, description="Maximum results to return")
