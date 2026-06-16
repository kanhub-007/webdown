"""Domain service interface for web search."""

from abc import ABC, abstractmethod

from webdown.core.domain.entities.search_result import SearchResult


class WebSearchService(ABC):
    """Searches the web for pages matching a query."""

    @abstractmethod
    def search(self, query: str, max_results: int = 20) -> list[SearchResult]:
        """Search the web and return matching results.

        Args:
            query: The search query string (non-empty).
            max_results: Maximum number of results to return (1-50).

        Returns:
            List of search results, ordered by relevance.

        Raises:
            SearchServiceError: If the search backend is unavailable.
        """
