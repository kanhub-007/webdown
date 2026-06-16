"""DTO for web search request."""

from dataclasses import dataclass


@dataclass
class SearchWebRequest:
    """Request DTO for web search use case."""

    query: str
    max_results: int = 20
