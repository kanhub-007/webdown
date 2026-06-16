"""DTO for web search response."""

from dataclasses import dataclass, field

from webdown.core.domain.entities.search_result import SearchResult


@dataclass
class SearchWebResponse:
    """Response DTO for web search use case."""

    query: str
    items: list[SearchResult] = field(default_factory=list)
