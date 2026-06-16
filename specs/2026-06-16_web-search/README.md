# Web Search — Specification Overview

**Date:** 2026-06-16
**Cynefin classification:** Clear (cause and effect obvious — web search is a well-understood domain; the `ddgs` library already handles the hard scraping problems)

## Why (Root Cause)

webdown can already render any URL to Markdown via Playwright, but users have no way to *discover* URLs through search. The gap: a user wants to research a topic (e.g., "Python async best practices"), find relevant pages via web search, then feed the result URLs into webdown's existing `convert_single_page`/`convert_all_pages` pipeline. Currently they must find URLs manually outside webdown.

## What (Summary)

Add a `search_web` capability that accepts a query string, returns search result URLs with titles and snippets, and exposes this via:
- **MCP tool** (`search_web`) for AI assistant integration
- **REST API endpoint** (`POST /web-index/api/search`) for programmatic use

The search is backed by the `ddgs` Python library (free, no API key), wrapped behind a domain interface (`WebSearchService`) so the backend can be swapped (e.g., to Brave Search API or SearXNG) without changing any other code.

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Use `ddgs` as first backend | Free, zero-setup, multi-engine (DuckDuckGo + Bing + Brave + more), actively maintained |
| Domain interface `WebSearchService` | Allows swapping to paid API (Brave) later without touching use case, presentation, or tests |
| Max 20 results default | Balances usefulness vs. DuckDuckGo rate limits (~10-20 req/min safe zone) |
| Synchronous execution | Search is fast (<3s typical); no need for background job infrastructure |
| Separate MCP tool + REST endpoint | Follows existing pattern (sitemap, markdown, rss all have both) |

## Files

- [01-story.md](01-story.md) — User story, context, non-goals
- [02-scenarios.md](02-scenarios.md) — Scenarios with Gherkin, I/O, Verify blocks
- [03-domain.md](03-domain.md) — Domain model (entities, interfaces, value objects)
- [04-implementation.md](04-implementation.md) — Step-by-step implementation guide
- [05-architecture.md](05-architecture.md) — Architecture decisions (ADR)
