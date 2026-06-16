"""Tests for the SearchWebUseCase."""

import pytest

from webdown.core.application.dto.search_web_request import SearchWebRequest
from webdown.core.application.use_cases.search_web import SearchWebUseCase
from webdown.core.domain.entities.search_result import SearchResult
from webdown.core.domain.exceptions import SearchServiceError
from webdown.core.domain.interfaces.web_search_service import WebSearchService


class InMemoryWebSearchService(WebSearchService):
    """Fake search service for testing — no real network calls."""

    def __init__(self, results: list[dict] | None = None, error: Exception | None = None) -> None:
        self._results = results or []
        self._error = error

    def search(self, query: str, max_results: int = 20) -> list[SearchResult]:
        if self._error:
            raise self._error
        return [
            SearchResult(title=r["title"], url=r["href"], snippet=r.get("body", ""))
            for r in self._results[:max_results]
        ]


class TestSearchWebUseCase:
    """Classical-style tests — real domain objects, fake at the boundary."""

    def test_happy_path_returns_results(self) -> None:
        """Search returns properly mapped domain entities."""
        fake = InMemoryWebSearchService([
            {"title": "Python Guide", "href": "https://example.com", "body": "Learn Python"}
        ])
        use_case = SearchWebUseCase(fake)

        result = use_case.execute(SearchWebRequest(query="python", max_results=10))

        assert len(result.items) == 1
        assert result.items[0].title == "Python Guide"
        assert result.items[0].url == "https://example.com"
        assert result.items[0].snippet == "Learn Python"
        assert result.query == "python"

    def test_none_query_raises_value_error(self) -> None:
        """None query raises ValueError, does not crash."""
        fake = InMemoryWebSearchService()
        use_case = SearchWebUseCase(fake)

        with pytest.raises(ValueError, match="query"):
            use_case.execute(SearchWebRequest(query=None, max_results=10))  # type: ignore[arg-type]

    def test_empty_query_raises_value_error(self) -> None:
        """Empty string query raises ValueError."""
        fake = InMemoryWebSearchService()
        use_case = SearchWebUseCase(fake)

        with pytest.raises(ValueError, match="query"):
            use_case.execute(SearchWebRequest(query="", max_results=10))

    def test_whitespace_query_raises_value_error(self) -> None:
        """Whitespace-only query raises ValueError."""
        fake = InMemoryWebSearchService()
        use_case = SearchWebUseCase(fake)

        with pytest.raises(ValueError, match="query"):
            use_case.execute(SearchWebRequest(query="   ", max_results=10))

    def test_max_results_clamped_to_50(self) -> None:
        """max_results > 50 is clamped to 50."""
        fake = InMemoryWebSearchService(
            [{"title": "t", "href": "https://x.com", "body": "b"}] * 60
        )
        use_case = SearchWebUseCase(fake)

        result = use_case.execute(SearchWebRequest(query="python", max_results=100))

        assert len(result.items) <= 50

    def test_max_results_within_limit_unchanged(self) -> None:
        """max_results within the limit is passed through unchanged."""
        fake = InMemoryWebSearchService(
            [{"title": "t", "href": "https://x.com", "body": "b"}] * 5
        )
        use_case = SearchWebUseCase(fake)

        result = use_case.execute(SearchWebRequest(query="python", max_results=5))

        assert len(result.items) == 5

    def test_no_results_returns_empty_list(self) -> None:
        """No matching results returns empty list, not an error."""
        fake = InMemoryWebSearchService([])
        use_case = SearchWebUseCase(fake)

        result = use_case.execute(SearchWebRequest(query="xyznonexistent", max_results=10))

        assert len(result.items) == 0
        assert result.query == "xyznonexistent"

    def test_service_error_is_wrapped(self) -> None:
        """Backend exceptions are wrapped in SearchServiceError."""
        fake = InMemoryWebSearchService(error=Exception("Rate limited"))
        use_case = SearchWebUseCase(fake)

        with pytest.raises(SearchServiceError, match="(?i)rate"):
            use_case.execute(SearchWebRequest(query="python", max_results=10))

    def test_default_max_results_is_20(self) -> None:
        """Default max_results is applied when not specified."""
        fake = InMemoryWebSearchService(
            [{"title": "t", "href": "https://x.com", "body": "b"}] * 30
        )
        use_case = SearchWebUseCase(fake)

        result = use_case.execute(SearchWebRequest(query="python"))

        assert len(result.items) <= 30  # uses default 20 from SearchWebRequest
        assert result.query == "python"


class TestSearchResultEntity:
    """Tests for the SearchResult domain entity."""

    def test_is_frozen_dataclass(self) -> None:
        """SearchResult is an immutable frozen dataclass."""
        from dataclasses import is_dataclass

        result = SearchResult(title="Test", url="https://example.com", snippet="A test")
        assert is_dataclass(result)

    def test_equality_by_value(self) -> None:
        """Two SearchResults with same values are equal."""
        a = SearchResult(title="T", url="https://x.com", snippet="s")
        b = SearchResult(title="T", url="https://x.com", snippet="s")
        assert a == b

    def test_different_values_not_equal(self) -> None:
        """SearchResults with different values are not equal."""
        a = SearchResult(title="T", url="https://x.com", snippet="s")
        b = SearchResult(title="T", url="https://y.com", snippet="s")
        assert a != b
