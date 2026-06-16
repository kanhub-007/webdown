# Implementation Guide — Web Search

Each step includes the exact file path, the code to write, how to verify, and common mistakes.

---

### Step 1: Create the SearchResult domain entity
**File:** `webdown/core/domain/entities/search_result.py`

```python
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
```

**Verify:** Import the class and check it's a frozen dataclass:
```python
from dataclasses import is_dataclass
from webdown.core.domain.entities.search_result import SearchResult

r = SearchResult(title="Test", url="https://example.com", snippet="A test")
assert is_dataclass(r)
assert r.title == "Test"
```

**Common mistake:** Do NOT import SQLAlchemy, Pydantic, or any ORM/framework here. This is a pure dataclass.

---

### Step 2: Create the WebSearchService domain interface
**File:** `webdown/core/domain/interfaces/web_search_service.py`

```python
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
```

**Verify:** `ruff check webdown/core/domain/interfaces/web_search_service.py` — must pass with zero errors.

**Common mistake:** Do NOT import `ddgs` or any concrete implementation here. This is a pure interface in the domain layer.

---

### Step 3: Create the domain exception
**File:** `webdown/core/domain/exceptions.py`

Add to the existing exceptions file (or create if it doesn't exist):

```python
class SearchServiceError(Exception):
    """Raised when the web search service is unavailable or fails."""
```

**Verify:** Import works, ruff passes.

---

### Step 4: Create the DTOs
**File:** `webdown/core/application/dto/search_web_request.py`

```python
"""DTO for web search request."""

from dataclasses import dataclass


@dataclass
class SearchWebRequest:
    """Request DTO for web search use case."""

    query: str
    max_results: int = 20
```

**File:** `webdown/core/application/dto/search_web_response.py`

```python
"""DTO for web search response."""

from dataclasses import dataclass, field

from webdown.core.domain.entities.search_result import SearchResult


@dataclass
class SearchWebResponse:
    """Response DTO for web search use case."""

    query: str
    items: list[SearchResult] = field(default_factory=list)
```

**Verify:** Import both, instantiate, ruff passes.

---

### Step 5: Create the SearchWebUseCase
**File:** `webdown/core/application/use_cases/search_web.py`

```python
"""Use case for searching the web."""

from webdown.core.application.dto.search_web_request import SearchWebRequest
from webdown.core.application.dto.search_web_response import SearchWebResponse
from webdown.core.domain.exceptions import SearchServiceError
from webdown.core.domain.interfaces.web_search_service import WebSearchService


class SearchWebUseCase:
    """Searches the web for pages matching a query."""

    MAX_RESULTS = 50

    def __init__(self, search_service: WebSearchService) -> None:
        """Initialize with the web search service."""
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
        query = request.query.strip()
        if not query:
            raise ValueError("Search query must be non-empty.")

        max_results = min(request.max_results, self.MAX_RESULTS)

        try:
            results = self._search_service.search(query=query, max_results=max_results)
        except Exception as exc:
            raise SearchServiceError(
                f"Search failed for query '{query}': {exc}"
            ) from exc

        return SearchWebResponse(query=query, items=results)
```

**Verify:** Write a quick test:
```python
from webdown.core.domain.entities.search_result import SearchResult
from webdown.core.application.use_cases.search_web import SearchWebUseCase
from webdown.core.application.dto.search_web_request import SearchWebRequest

# Use an anonymous in-memory implementation for the quick sanity check
class _FakeService:
    def search(self, query, max_results=20):
        return [SearchResult(title="T", url="https://x.com", snippet="s")]

use_case = SearchWebUseCase(_FakeService())
result = use_case.execute(SearchWebRequest(query="test"))
assert len(result.items) == 1
```

**Common mistake:** Do NOT import `ddgs` or `DDGSWebSearchService` here. The use case depends ONLY on the abstract `WebSearchService` interface.

---

### Step 6: Implement the DDGSWebSearchService
**File:** `webdown/infrastructure/services/ddgs_web_search_service.py`

```python
"""DDGS-backed web search service implementation."""

import logging

from ddgs import DDGS
from ddgs.exceptions import RatelimitException, TimeoutException

from webdown.core.domain.entities.search_result import SearchResult
from webdown.core.domain.interfaces.web_search_service import WebSearchService

logger = logging.getLogger(__name__)


class DDGSWebSearchService(WebSearchService):
    """Web search service backed by the ddgs library (DuckDuckGo/Bing/Brave)."""

    def __init__(self) -> None:
        """Initialize the DDGS client."""
        self._ddgs = DDGS()

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
                backend="html",  # html.duckduckgo.com — most reliable
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
```

**Verify:** Run a quick integration test (requires network):
```python
from webdown.infrastructure.services.ddgs_web_search_service import DDGSWebSearchService

service = DDGSWebSearchService()
results = service.search("test query", max_results=3)
assert len(results) > 0
assert results[0].url.startswith("http")
```

**Common mistake:** Don't forget to filter out results missing `href` or `title`. The ddgs library can return incomplete entries.

---

### Step 7: Add factory functions
**File:** `webdown/startup/service_factory.py` — add:

```python
from webdown.infrastructure.services.ddgs_web_search_service import DDGSWebSearchService

@lru_cache(maxsize=1)
def create_web_search_service() -> DDGSWebSearchService:
    """Create the web search service."""
    return DDGSWebSearchService()
```

**File:** `webdown/startup/use_case_factory.py` — add:

```python
from webdown.core.application.use_cases.search_web import SearchWebUseCase

@lru_cache(maxsize=1)
def create_search_web_use_case() -> SearchWebUseCase:
    """Create the web search use case."""
    return SearchWebUseCase(create_web_search_service())
```

**Verify:** `ruff check webdown/startup/` passes.

---

### Step 8: Create the MCP tool
**File:** `webdown/presentation/mcp/tools/search.py`

```python
"""MCP tools — web search."""

from webdown.core.application.dto.search_web_request import SearchWebRequest
from webdown.core.domain.exceptions import SearchServiceError
from webdown.startup.use_case_factory import create_search_web_use_case


def register_search_tools(server: object) -> None:
    """Register web search tools on the MCP server."""

    @server.tool(
        description=(
            "Search the web and return matching page URLs with titles and snippets. "
            "Use this to discover pages about a topic, then feed the URLs into "
            "convert_single_page or convert_all_pages to convert them to Markdown. "
            "Returns up to 20 results by default (max 50)."
        ),
    )
    def search_web(query: str, max_results: int = 20) -> dict:
        """Search the web for pages matching a query."""
        try:
            use_case = create_search_web_use_case()
            result = use_case.execute(
                SearchWebRequest(query=query, max_results=max_results)
            )
            return {
                "query": result.query,
                "results": [
                    {
                        "title": item.title,
                        "url": item.url,
                        "snippet": item.snippet,
                    }
                    for item in result.items
                ],
                "total_count": len(result.items),
            }
        except ValueError as e:
            return {"error": str(e), "query": query, "results": [], "total_count": 0}
        except SearchServiceError as e:
            return {"error": str(e), "query": query, "results": [], "total_count": 0}
```

**File:** `webdown/presentation/mcp/server.py` — register the tools:

```python
from webdown.presentation.mcp.tools.search import register_search_tools

# In the server creation function, add:
register_search_tools(server)
```

**Verify:** Start the MCP server and call the tool.

---

### Step 9: Create the REST API endpoint
**File:** `webdown/presentation/api/models/search_request.py`

```python
"""Pydantic model for web search request."""

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request model for web search."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    max_results: int = Field(default=20, ge=1, le=50, description="Maximum results to return")
```

**File:** `webdown/presentation/api/models/search_response.py`

```python
"""Pydantic model for web search response."""

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    """A single search result item."""

    title: str
    url: str
    snippet: str


class SearchResponse(BaseModel):
    """Response model for web search."""

    query: str
    results: list[SearchResultItem]
    total_count: int
```

**File:** `webdown/presentation/api/routes/search.py`

```python
"""Web search endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Request

from webdown.core.application.dto.search_web_request import SearchWebRequest
from webdown.core.application.use_cases.search_web import SearchWebUseCase
from webdown.core.domain.exceptions import SearchServiceError
from webdown.presentation.api.models.search_request import SearchRequest
from webdown.presentation.api.models.search_response import SearchResponse, SearchResultItem

router = APIRouter(prefix="/api/search", tags=["Web Search"])


def get_search_web_use_case(request: Request) -> SearchWebUseCase:
    return request.app.state.search_web_use_case


@router.post("", response_model=SearchResponse)
async def search_web(
    request: SearchRequest,
    use_case: SearchWebUseCase = Depends(get_search_web_use_case),
):
    """Search the web for pages matching a query.

    Returns up to max_results pages with titles, URLs, and snippets.
    Use the returned URLs with the markdown conversion endpoints
    to convert discovered pages to Markdown.
    """
    try:
        dto = SearchWebRequest(query=request.query, max_results=request.max_results)
        result = use_case.execute(dto)
        return SearchResponse(
            query=result.query,
            results=[
                SearchResultItem(title=item.title, url=item.url, snippet=item.snippet)
                for item in result.items
            ],
            total_count=len(result.items),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except SearchServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Register the router** in `webdown/presentation/api/routes/__init__.py` and wire `search_web_use_case` onto `app.state` in `webdown/startup/api.py`.

---

### Step 10: Write the tests
**File:** `tests/test_application/test_search_web.py`

```python
"""Tests for the SearchWebUseCase."""

import pytest

from webdown.core.application.dto.search_web_request import SearchWebRequest
from webdown.core.application.use_cases.search_web import SearchWebUseCase
from webdown.core.domain.entities.search_result import SearchResult
from webdown.core.domain.exceptions import SearchServiceError


class InMemoryWebSearchService:
    """Fake search service for testing."""

    def __init__(self, results: list[dict] | None = None, error: Exception | None = None):
        self._results = results or []
        self._error = error
        self.search_calls: list[tuple] = []

    def search(self, query: str, max_results: int = 20) -> list[SearchResult]:
        self.search_calls.append((query, max_results))
        if self._error:
            raise self._error
        return [
            SearchResult(title=r["title"], url=r["href"], snippet=r.get("body", ""))
            for r in self._results[:max_results]
        ]


class TestSearchWebUseCase:
    def test_happy_path_returns_results(self):
        fake = InMemoryWebSearchService([
            {"title": "Python Guide", "href": "https://example.com", "body": "Learn Python"}
        ])
        use_case = SearchWebUseCase(fake)
        result = use_case.execute(SearchWebRequest(query="python", max_results=10))

        assert len(result.items) == 1
        assert result.items[0].title == "Python Guide"
        assert result.items[0].url == "https://example.com"

    def test_empty_query_raises_value_error(self):
        fake = InMemoryWebSearchService()
        use_case = SearchWebUseCase(fake)

        with pytest.raises(ValueError, match="query"):
            use_case.execute(SearchWebRequest(query="", max_results=10))

    def test_whitespace_query_raises_value_error(self):
        fake = InMemoryWebSearchService()
        use_case = SearchWebUseCase(fake)

        with pytest.raises(ValueError, match="query"):
            use_case.execute(SearchWebRequest(query="   ", max_results=10))

    def test_max_results_clamped_to_50(self):
        fake = InMemoryWebSearchService(
            [{"title": "t", "href": "https://x.com", "body": "b"}] * 60
        )
        use_case = SearchWebUseCase(fake)
        result = use_case.execute(SearchWebRequest(query="python", max_results=100))

        assert len(result.items) <= 50

    def test_no_results_returns_empty_list(self):
        fake = InMemoryWebSearchService([])
        use_case = SearchWebUseCase(fake)
        result = use_case.execute(SearchWebRequest(query="xyznonexistent", max_results=10))

        assert len(result.items) == 0
        assert result.query == "xyznonexistent"

    def test_service_error_is_wrapped(self):
        from ddgs.exceptions import RatelimitException

        fake = InMemoryWebSearchService(error=RatelimitException("Rate limited"))
        use_case = SearchWebUseCase(fake)

        with pytest.raises(SearchServiceError, match="rate"):
            use_case.execute(SearchWebRequest(query="python", max_results=10))
```

**Verify:** `pytest tests/test_application/test_search_web.py -v` — all tests pass.

**Common mistake:** Do NOT mock `WebSearchService` with `unittest.mock.MagicMock`. Always use a fake/in-memory implementation (see `InMemoryWebSearchService` above). Assert on outcomes, not on whether `.search()` was called.
