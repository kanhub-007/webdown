"""Pydantic model for a single search result item."""

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    """A single search result item."""

    title: str
    url: str
    snippet: str
