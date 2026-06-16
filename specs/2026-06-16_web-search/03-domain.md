# Domain Model — Web Search

## Ubiquitous Language (Glossary)

| Term | Definition | Synonyms (merge) | Homonyms (split) |
|------|-----------|------------------|------------------|
| Search Query | A user-supplied text string to find web pages about | query, search term, keywords | — |
| Search Result | A single web page match: title, URL, and text snippet | result, hit, entry | Not: job result, calculation result |
| Snippet | A short text extract from the page content shown in search results | body, description, excerpt | — |
| Search Backend | The concrete engine that performs the search (DuckDuckGo, Bing, Brave) | engine, provider | — |
| Rate Limit | A temporary block from the search engine for too many requests | throttle, cooldown | — |

## Concept Taxonomy

| Concept | Classification | Why |
|---------|---------------|-----|
| SearchResult | Entity (immutable) | Has identity (URL is unique), but immutable after creation — closer to a Value Object. Treated as an Entity for clarity. |
| SearchQuery | Value Object | Defined entirely by query string + max_results; no identity |
| WebSearchService | Domain Service interface | Stateless operation that spans external search engines |
| DDGSWebSearchService | Infrastructure Adapter | Wraps the `ddgs` library behind the domain interface |
| SearchWebRequest | DTO | Crosses boundary from presentation to application |
| SearchWebResponse | DTO | Crosses boundary from application to presentation |

## Entities

| Entity | Fields | Behaviour | Persisted? |
|--------|--------|-----------|------------|
| SearchResult | title (str), url (str), snippet (str) | Pure data, no behaviour | No — ephemeral |

## Value Objects

| Value Object | Fields | Used where |
|-------------|--------|------------|
| SearchQuery | query (str), max_results (int) | Input to WebSearchService |

## Domain Events

None — search is a synchronous read operation with no side effects.

## Interfaces (for DI)

| Interface | Methods | Implemented by |
|-----------|---------|----------------|
| WebSearchService | `search(query: str, max_results: int) -> list[SearchResult]` | DDGSWebSearchService, InMemoryWebSearchService (tests) |

## Invariants (Always-True Rules)

| # | Invariant | Enforcement point |
|---|-----------|-------------------|
| 1 | query must be non-empty after stripping whitespace | SearchWebUseCase.execute() |
| 2 | max_results must be between 1 and 50 | SearchWebRequest DTO validation |
| 3 | SearchResult.url must be a valid absolute URL | DDGSWebSearchService (post-filter) |
| 4 | SearchResult.title must be non-empty | DDGSWebSearchService (post-filter) |

## Entity Lifecycles

SearchResult is immutable — no lifecycle transitions.

## Entity vs ORM separation

- **Domain entity:** `webdown/core/domain/entities/search_result.py` — pure `@dataclass`, no framework deps
- **ORM model:** None — search results are ephemeral, not persisted
- **Mapper:** None needed
