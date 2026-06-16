"""Domain entity for a single web search result."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResult:
    """A single result from a web search query.

    Immutable — once a search result is created, it does not change.
    """

    title: str
    url: str
    snippet: str
