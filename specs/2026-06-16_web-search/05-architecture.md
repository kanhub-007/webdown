# Architecture Decisions — Web Search

---

## ADR-1: Use `ddgs` library as first backend, with domain interface for swappability

**Context:** We need a search backend. Options: DuckDuckGo Instant Answer API (no web results), `ddgs` Python library (scraped, free, multi-engine), Brave Search API (2k queries/month free tier), Google Custom Search (100/day free, needs API key), SearXNG (self-hosted).

**Decision:** Use `ddgs` as the first implementation behind a `WebSearchService` domain interface.

**Consequences:**
- ✅ Zero setup, zero cost — works immediately after `pip install ddgs`
- ✅ Multi-engine fallback: DuckDuckGo → Bing → Brave → etc. (the library tries multiple backends)
- ✅ Swappable: wrap in domain interface, can replace with Brave API later without changing use case/MCP/API code
- ❌ No SLA — DuckDuckGo can change HTML structure, breaking the scraper
- ❌ Rate limits — ~10-20 req/min safe zone; aggressive use triggers `RatelimitException`
- ❌ Results may vary in quality vs. paid API

---

## ADR-2: Clamp max_results silently instead of raising an error

**Context:** The `ddgs` library doesn't limit `max_results` but DuckDuckGo rate limits make large requests impractical. The meaningful maximum is ~50 (pagination beyond that returns no new results).

**Decision:** Clamp `max_results` to 50 silently. If user passes 100, they get 50.

**Alternatives considered:**
1. Raise `ValueError` for >50 — more explicit but requires user to know the limit
2. Return as many as available without clamping — risks rate limits and slow responses
3. Clamp silently — most user-friendly, least surprising

**Consequences:**
- ✅ User-friendly: just works, no configuration needed
- ❌ Less explicit: user might not realize their `max_results=100` was clamped
- ✅ Return response includes `total_count` so the user sees how many they got

---

## ADR-3: Synchronous execution (no background job)

**Context:** Markdown generation uses background jobs because Playwright rendering is slow (seconds per page). Search via `ddgs` is fast (~1-3 seconds per query).

**Decision:** Execute search synchronously. The use case returns results immediately. No `BackgroundProcessor` involvement.

**Consequences:**
- ✅ Simpler architecture: no job tracking, progress polling, or `start_*/get_progress` pattern
- ✅ Faster UX: results returned in a single request/response cycle
- ❌ If search were ever slow (>10s), this would block. Mitigated by the `timeout` parameter in ddgs.

---

## ADR-4: Search results are NOT auto-converted to Markdown

**Context:** A tempting design would be "search → automatically convert all result pages to Markdown." This couples search and conversion.

**Decision:** Keep search and conversion as separate, composable operations. Search returns URLs + metadata only. The user explicitly calls `convert_single_page` or `convert_all_pages` on the URLs they want.

**Consequences:**
- ✅ Composability: search + convert, search + filter + convert, search + convert single, etc.
- ✅ Alignment with Unix philosophy: one tool does one thing well
- ✅ No surprise costs: user controls which URLs get the expensive Playwright rendering
- ❌ Two-step workflow instead of one-step — mitigated by MCP tool descriptions guiding the AI assistant
