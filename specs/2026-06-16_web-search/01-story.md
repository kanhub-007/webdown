# Web Search

## User Story

As a developer or AI assistant using webdown, I want to search the web for pages matching a query and get back URLs, titles, and snippets, so that I can discover relevant content and feed those URLs into webdown's existing Markdown conversion pipeline.

## Context

webdown currently excels at converting known URLs to Markdown — it renders pages with Playwright, handles cookie consent, extracts tables/code blocks/alerts, and outputs clean Markdown. But there's no way to *find* pages from within webdown itself. Users must locate URLs externally (browser, another search tool), then paste them into webdown.

Adding web search closes this gap. A user can now: search for "Python async best practices" → get 10 relevant URLs → feed those URLs into `convert_single_page` or `convert_all_pages` → receive Markdown. The entire research-and-convert workflow becomes self-contained.

The `ddgs` Python library (formerly `duckduckgo-search`) provides free, programmatic access to DuckDuckGo, Bing, Brave, and other search engines. By wrapping it behind a domain interface, the backend can be swapped later (e.g., to Brave Search API for higher limits) without touching the use case or presentation layers.

The feature follows webdown's existing patterns: domain interface → infrastructure implementation → use case → MCP tool + REST endpoint.

## Non-Goals

Things explicitly NOT being built in this iteration:

- **Image/video/news search** — Text search only. The `ddgs` library supports these, but they're out of scope for v1.
- **Pagination / offset** — Single page of results. `max_results` controls count (default 20).
- **Automatic Markdown conversion of search results** — Search returns URLs + metadata. The user explicitly calls `convert_single_page` or `convert_all_pages` on the URLs they want. Search and conversion remain separate, composable operations.
- **Search history / persistence** — Queries and results are ephemeral, not stored.
- **Paid API backends** (Brave, Google CSE, SerpAPI) — V1 uses only the free `ddgs` library. The interface supports swapping later.
- **Spelling correction / "did you mean"** — The search engine may provide this naturally; we don't add our own layer.
- **Date-filtered search** — `ddgs` supports `timelimit` (d/w/m/y), but this is deferred to v2.
