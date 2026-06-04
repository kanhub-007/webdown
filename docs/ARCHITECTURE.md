# Architecture Guide

WebDown follows **Clean Architecture** with four layers plus a composition
root. Dependencies flow **inward** only.

## Layers

```
┌──────────────────────────────────────────────────────┐
│  presentation/     REST routes, MCP tools,            │
│                    Streamlit UI, pi extension         │
│                    Can import: application, domain,   │
│                    infrastructure (for adapters)      │
├──────────────────────────────────────────────────────┤
│  startup/          Composition root, DI factories     │
│                    Can import: EVERYTHING             │
├──────────────────────────────────────────────────────┤
│  core/application/ Use cases, DTOs                   │
│                    Can import: domain ONLY            │
├──────────────────────────────────────────────────────┤
│  core/domain/      Entities, interfaces, pure logic  │
│                    Can import: stdlib, abc, dataclasses│
├──────────────────────────────────────────────────────┤
│  infrastructure/   SQLite repos, Playwright,         │
│                    BeautifulSoup, feedparser          │
│                    Can import: domain ONLY            │
└──────────────────────────────────────────────────────┘
```

## Package Layout

### `core/domain/entities/`

Pure dataclasses — no frameworks, no ORM, no Pydantic:

- `MarkdownFile` — generated markdown content and metadata
- `MarkdownFileMetadata` — metadata without content (list views)
- `MarkdownJob` — job progress tracking
- `SitemapUrl` — sitemap URL entry
- `WebsitePages` — discovered pages container
- `FeedItem` — RSS/Atom feed item

### `core/domain/interfaces/`

ABC interfaces that use cases depend on:

- `MarkdownJobRepository` — job progress persistence
- `MarkdownFileRepository` — markdown file persistence
- `SitemapDiscoveryService` — sitemap crawling
- `SiteMetadataService` — metadata file discovery
- `PageRenderer` — Playwright rendering
- `HtmlToMarkdownConverter` — HTML-to-Markdown conversion
- `GitHubRepositoryProcessor` — repository ingestion
- `RssFeedAggregator` — RSS aggregation
- `BackgroundProcessor` — long-running task dispatch

### `core/application/use_cases/`

Use cases (interactors) orchestrate domain objects. Each depends only on
domain interfaces via constructor injection.

| Use Case | Responsibility |
|----------|---------------|
| `ExploreSitemapUseCase` | Discover pages from sitemaps |
| `AggregateRssFeedsUseCase` | Aggregate configured RSS feeds |
| `GenerateAllPagesMarkdownUseCase` | Convert sitemap-discovered pages to markdown |
| `GenerateSinglePageMarkdownUseCase` | Convert one URL to markdown |
| `GenerateGitHubRepoMarkdownUseCase` | Convert a GitHub repository |
| `StartAllPagesMarkdownJobUseCase` | Create job + schedule all-pages generation |
| `StartSinglePageMarkdownJobUseCase` | Create job + schedule single-page generation |
| `StartGitHubRepoMarkdownJobUseCase` | Create job + schedule GitHub repo generation |
| `GetJobProgressUseCase` | Query job progress |
| `GetMarkdownFileUseCase` | Retrieve generated markdown |
| `ListMarkdownFilesUseCase` | List generated files (metadata only) |

### `core/application/dto/`

Data transfer objects crossing layer boundaries:

| DTO | Direction |
|-----|-----------|
| `SitemapExploreRequest` | input |
| `SitemapExploreResult` | output |
| `GenerateAllPagesRequest` | input |
| `GenerateSinglePageRequest` | input |
| `GenerateGitHubRepoRequest` | input |
| `JobResult` | output |
| `JobProgressResult` | output |
| `MarkdownFileMetadataResult` | output |

### `infrastructure/`

Concrete implementations of domain interfaces:

- `repositories/` — SQLite-backed repositories with connection factory
- `repositories/mappers/` — row-to-entity mapping functions
- `services/` — Playwright, BeautifulSoup, feedparser, requests, gitingest
- `services/consent_handlers/` — cookie consent Chain of Responsibility
- `database/` — schema initialization

### `presentation/`

Adapters to the outside world:

- `api/routes/` — FastAPI route handlers (thin — delegate to use cases)
- `api/models/` — Pydantic request/response models
- `api/presenters/` — DTO-to-Pydantic model converters
- `api/adapters/` — FastAPI-specific adapters (background processor)
- `mcp/server.py` — FastMCP server creation
- `mcp/tools/` — MCP tool implementations
- `streamlit/app.py` — Streamlit web UI

### `startup/`

Composition root — wires everything together:

- `app_factory.py` — FastAPI app creation + route wiring
- `api.py` — API entry point (uvicorn runner)
- `mcp.py` — MCP entry point (FastMCP runner)
- `repository_factory.py` — repository wiring
- `service_factory.py` — service wiring
- `use_case_factory.py` — use case wiring

## Design Patterns

| Pattern | Where Applied |
|---------|--------------|
| Constructor DI | All use cases + repositories + services |
| Repository | SQLite repos implementing ABC interfaces |
| Strategy | Services behind interfaces, swappable via factories |
| Factory | 4 factory modules in `startup/` |
| DTO | 8 DTOs for layer boundary crossing |
| Presenter / Facade | 5 presenters in `presentation/api/presenters/` |
| Background Processor | Domain interface + FastAPI adapter |
| Chain of Responsibility | Cookie consent handlers |
| Template Method | Page rendering (`_process_page`) |
| Pipeline / Extract Method | HTML-to-Markdown converter |

## Data Flow

```
HTTP request → Pydantic model → Input DTO → Use Case → Output DTO → Presenter → Pydantic model → HTTP response
```

Routes never construct models directly — presenters handle conversion.

## Dependency Rules

| Layer | May Import |
|-------|-----------|
| `startup/` | Everything |
| `presentation/` | `core/application`, `core/domain`, `infrastructure` (adapters) |
| `core/application/` | `core/domain` only |
| `core/domain/` | stdlib, abc, dataclasses |
| `infrastructure/` | `core/domain` only |
