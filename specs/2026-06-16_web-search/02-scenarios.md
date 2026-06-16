# Scenarios — Web Search

---

### Scenario: Happy path — basic text search
**Priority:** Must
**Slice:** 1

**Gherkin:**
  Given the web search service is available
  When  the user searches for "python async programming"
  Then  a list of search results is returned, each with title, url, and snippet

**Input table:**
| Field       | Type      | Example                  | Constraints             |
|-------------|-----------|--------------------------|-------------------------|
| query       | string    | "python async programming" | Required, non-empty, max 500 chars |
| max_results | int       | 10                       | Optional, 1–50, default 20 |

**Expected output / state change:**
| Assertion                                              | How to verify                     |
|--------------------------------------------------------|-----------------------------------|
| Result list length <= max_results                      | `len(results) <= 20`              |
| Each result has non-empty title, url, snippet          | Loop and assert                   |
| URLs start with http:// or https://                    | `r.url.startswith("http")`        |
| Results are ranked (first result most relevant)        | First result's title contains query terms |

**Verify (Classical school, black-box):**
```python
# Use a fake, not a mock
fake_search_service = InMemoryWebSearchService([
    {"title": "Python Async Programming Guide", "href": "https://example.com/async", "body": "Learn async..."},
])
use_case = SearchWebUseCase(fake_search_service)
results = use_case.execute(SearchWebRequest(query="python async", max_results=5))

assert len(results.items) == 1
assert results.items[0].title == "Python Async Programming Guide"
assert results.items[0].url == "https://example.com/async"
assert results.query == "python async"
# Do NOT: mock_search_service.search.assert_called_once()
```

**Also test:**
- Query with special characters ("C++ templates") → results returned normally
- Query with spaces only → raises ValueError
- max_results = 1 → returns exactly 1 result

---

### Scenario: Empty or blank query
**Priority:** Must
**Slice:** 1

**Gherkin:**
  Given the web search service is available
  When  the user provides an empty or whitespace-only query
  Then  a ValueError is raised with a descriptive message

**Input table:**
| Field       | Type      | Example  | Constraints       |
|-------------|-----------|----------|-------------------|
| query       | string    | ""       | Empty or whitespace |

**Expected output / state change:**
| Assertion                           | How to verify              |
|-------------------------------------|----------------------------|
| ValueError raised                   | `pytest.raises(ValueError)`|
| Message contains "query"            | String check               |

**Verify:**
```python
use_case = SearchWebUseCase(InMemoryWebSearchService([]))

with pytest.raises(ValueError, match="query"):
    use_case.execute(SearchWebRequest(query="", max_results=10))

with pytest.raises(ValueError, match="query"):
    use_case.execute(SearchWebRequest(query="   ", max_results=10))
```

**Also test:**
- None query → raises ValueError

---

### Scenario: max_results exceeds limit
**Priority:** Must
**Slice:** 1

**Gherkin:**
  Given the web search service is available
  When  the user requests more than 50 results
  Then  max_results is clamped to 50 (or an error is raised)

**Input table:**
| Field       | Type      | Example   | Constraints       |
|-------------|-----------|-----------|-------------------|
| query       | string    | "python"  | Valid              |
| max_results | int       | 100       | Exceeds maximum    |

**Expected output / state change:**
| Assertion                           | How to verify              |
|-------------------------------------|----------------------------|
| max_results is clamped to 50       | Inspect use case logic     |
| Or ValueError for max_results > 50 | `pytest.raises(ValueError)`|

**Design decision:** Clamp silently to 50 rather than raising an error — this is more user-friendly.
See [05-architecture.md](05-architecture.md) ADR-2.

**Verify:**
```python
use_case = SearchWebUseCase(InMemoryWebSearchService([{"title": "t", "href": "https://x.com", "body": "b"}] * 50))

results = use_case.execute(SearchWebRequest(query="python", max_results=100))
assert len(results.items) <= 50
```

---

### Scenario: Search service returns no results
**Priority:** Must
**Slice:** 1

**Gherkin:**
  Given the web search service is available
  When  the user searches for a query that matches nothing
  Then  an empty result list is returned (not an error)

**Input table:**
| Field       | Type      | Example                     | Constraints       |
|-------------|-----------|-----------------------------|-------------------|
| query       | string    | "xyznonexistent12345abcde"  | Valid              |

**Expected output / state change:**
| Assertion                           | How to verify              |
|-------------------------------------|----------------------------|
| Empty items list                    | `len(results.items) == 0`  |
| results.query preserved             | `results.query == query`   |
| No exception raised                 | Normal return              |

**Verify:**
```python
use_case = SearchWebUseCase(InMemoryWebSearchService([]))
results = use_case.execute(SearchWebRequest(query="xyznonexistent", max_results=10))

assert len(results.items) == 0
assert results.query == "xyznonexistent"
```

---

### Scenario: Search service is unavailable (rate limited or down)
**Priority:** Should
**Slice:** 2

**Gherkin:**
  Given the DuckDuckGo search service is rate-limited
  When  the user performs a search
  Then  a SearchServiceError is raised with a descriptive message

**Input table:**
| Field       | Type      | Example    | Constraints       |
|-------------|-----------|------------|-------------------|
| query       | string    | "python"   | Valid              |

**Expected output / state change:**
| Assertion                           | How to verify              |
|-------------------------------------|----------------------------|
| SearchServiceError raised           | `pytest.raises(SearchServiceError)` |
| Message mentions "rate limit" or "unavailable" | String check    |

**Verify:**
```python
failing_service = FailingWebSearchService(error=RatelimitException("Rate limited"))
use_case = SearchWebUseCase(failing_service)

with pytest.raises(SearchServiceError, match="rate"):
    use_case.execute(SearchWebRequest(query="python", max_results=10))
```

**Also test:**
- TimeoutException → SearchServiceError with "timeout" message
- Generic DDGSException → SearchServiceError with original message wrapped

---

### Scenario: MCP tool exposes search_web
**Priority:** Must
**Slice:** 1

**Gherkin:**
  Given the MCP server is running
  When  an AI assistant calls the `search_web` tool with a query
  Then  a JSON result with results array is returned

**Input table:**
| Field       | Type      | Example                  | Constraints             |
|-------------|-----------|--------------------------|-------------------------|
| query       | string    | "python async"           | Required, non-empty     |
| max_results | int       | 10                       | Optional, default 20    |

**Expected output:**
```json
{
  "query": "python async",
  "results": [
    {"title": "Python Async Guide", "url": "https://...", "snippet": "Learn async..."}
  ],
  "total_count": 1
}
```

**Verify:** Register the MCP tool and call it with test input. Assert the response structure matches.

---

### Scenario: REST API exposes POST /web-index/api/search
**Priority:** Must
**Slice:** 1

**Gherkin:**
  Given the FastAPI server is running
  When  a client sends POST /web-index/api/search with query and max_results
  Then  a 200 response with JSON search results is returned

**Input table (request body):**
| Field       | Type      | Example                  | Constraints             |
|-------------|-----------|--------------------------|-------------------------|
| query       | string    | "python async"           | Required, non-empty     |
| max_results | int       | 10                       | Optional, 1–50, default 20 |

**Expected output (response):**
| Status | Body                                                       |
|--------|------------------------------------------------------------|
| 200    | `{"query": "...", "results": [...], "total_count": N}`    |
| 422    | Validation error (empty query)                              |
| 500    | Search service error                                        |

**Verify:** Use `TestClient` to POST to the endpoint. Assert status code and response structure.

---

### Scenario: Domain entity SearchResult is a pure dataclass
**Priority:** Must
**Slice:** 1

**Gherkin:**
  Given the domain entity is defined
  When  a SearchResult is constructed
  Then  it holds title, url, and snippet with no framework dependencies

**Verify:**
```python
from webdown.core.domain.entities.search_result import SearchResult

result = SearchResult(
    title="Python Guide",
    url="https://example.com",
    snippet="Learn Python async..."
)

assert result.title == "Python Guide"
assert result.url == "https://example.com"
# This must work: no ORM, no framework imports
from dataclasses import is_dataclass
assert is_dataclass(result)
```

---

### Scenario: Search results feed into existing convert_single_page
**Priority:** Should
**Slice:** 2

**Gherkin:**
  Given a search returns URLs
  When  the user takes a URL from search results and passes it to convert_single_page
  Then  the page is rendered and converted to Markdown as normal

This is a **composability** scenario — it verifies that search results are compatible with existing conversion tools without any special handling.

**Verify:** Search → take first result URL → call convert_single_page with that URL → assert Markdown output is non-empty.
