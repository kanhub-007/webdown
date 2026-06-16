"""Use case for searching the web."""

from webdown.core.application.dto.search_web_request import SearchWebRequest
from webdown.core.application.dto.search_web_response import SearchWebResponse
from webdown.core.domain.exceptions import SearchServiceError
from webdown.core.domain.interfaces.web_search_service import WebSearchService


class SearchWebUseCase:
    """Searches the web for pages matching a query."""

    MAX_RESULTS = 50

    def __init__(self, search_service: WebSearchService) -> None:
        """Initialize with the web search service.

        Args:
            search_service: The search service implementation (injected).
        """
        self._search_service = search_service

    def execute(self, request: SearchWebRequest) -> SearchWebResponse:
        """Execute the search and return results.

        Args:
            request: The search request with query and max_results.

        Returns:
            SearchWebResponse with results.

        Raises:
            ValueError: If query is empty or whitespace-only.
            SearchServiceError: If the search backend fails.
        """
        if not request.query or not request.query.strip():
            raise ValueError("Search query must be non-empty.")
        query = request.query.strip()

        if request.max_results < 1:
            raise ValueError("max_results must be at least 1.")
        max_results = min(request.max_results, self.MAX_RESULTS)

        try:
            results = self._search_service.search(query=query, max_results=max_results)
        except SearchServiceError:
            raise
        except Exception as exc:
            raise SearchServiceError(
                f"Search failed for query '{query}': {exc}"
            ) from exc

        return SearchWebResponse(query=query, items=results)
