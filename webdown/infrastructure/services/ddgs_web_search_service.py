"""DDGS-backed web search service implementation."""

from ddgs import DDGS
from ddgs.exceptions import RatelimitException, TimeoutException

from webdown.core.domain.entities.search_result import SearchResult
from webdown.core.domain.exceptions import SearchServiceError
from webdown.core.domain.interfaces.web_search_service import WebSearchService


class DDGSWebSearchService(WebSearchService):
    """Web search service backed by the ddgs library (DuckDuckGo/Bing/Brave)."""

    def __init__(self, ddgs_client: DDGS | None = None) -> None:
        """Initialize with an optional DDGS client (injectable for testing).

        Args:
            ddgs_client: A DDGS instance. When None, a default client is created.
        """
        self._ddgs: DDGS = ddgs_client if ddgs_client is not None else DDGS()

    def search(self, query: str, max_results: int = 20) -> list[SearchResult]:
        """Search the web using DDGS.

        Args:
            query: Search query string.
            max_results: Maximum results to return.

        Returns:
            List of SearchResult domain entities.

        Raises:
            SearchServiceError: On rate limit or other failure.
        """
        try:
            raw_results = self._ddgs.text(
                query,
                max_results=max_results,
                backend="html",
                safesearch="moderate",
            )
        except RatelimitException as exc:
            raise SearchServiceError(
                "Search backend is rate-limited. Please wait and try again."
            ) from exc
        except TimeoutException as exc:
            raise SearchServiceError(
                "Search backend timed out. Please try again."
            ) from exc
        except Exception as exc:
            raise SearchServiceError(
                f"Search backend error: {exc}"
            ) from exc

        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("href", ""),
                snippet=r.get("body", ""),
            )
            for r in raw_results
            if r.get("href") and r.get("title")
        ]
