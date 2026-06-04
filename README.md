# WebDown

Convert websites to Markdown, explore sitemaps, and aggregate RSS feeds — via REST API, MCP server, or Streamlit UI.

## Quick Start

```bash
pip install -r requirements.txt
playwright install chromium
python run_api.py            # API → http://localhost:8000/docs
python run_mcp.py            # MCP → stdio (or http with WEBDOWN_TRANSPORT=http)
python run_streamlit.py      # Streamlit UI → http://localhost:8501
```

Or via Docker:

```bash
docker-compose up --build
```

## Features

| Feature | API | MCP | Streamlit |
|---------|-----|-----|-----------|
| Sitemap exploration | POST /web-index/api/sitemap/explore | `explore_sitemap` | Sitemap Explorer tab |
| Convert single page | POST /web-convert/api/markdown/generate-single | `convert_single_page` | Single Page Scraper tab |
| Convert full website | POST /web-convert/api/markdown/generate-all | `convert_all_pages` | Full Site Scraper tab |
| Convert GitHub repo | POST /web-convert/api/markdown/generate-github-repo | `convert_github_repo` | — |
| Progress tracking | GET /web-convert/api/markdown/progress/{id} | `get_job_progress` | Inline |
| Download markdown | GET /web-convert/api/markdown/download/{id} | `download_markdown` | Download button |
| List files | GET /web-convert/api/markdown/list | `list_markdown_files` | — |
| RSS aggregation | GET /rss/api/rss/aggregate | `aggregate_rss_feeds` | — |
| Generate job ID | — | `generate_job_id` | — |

## Architecture

WebDown follows clean architecture:

```
presentation/   → REST routes, MCP tools, Streamlit UI
startup/        → Composition root (factory wiring)
core/application/ → Use cases (orchestration), DTOs
core/domain/    → Entities, interfaces (pure logic)
infrastructure/ → SQLite repos, Playwright, BeautifulSoup, feedparser
```

All dependencies point inward. The domain layer knows nothing about frameworks or infrastructure.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full architecture guide.

## Running

### API server

```bash
python run_api.py
```

Configure via `.env`:

```bash
API_HOST=0.0.0.0
API_PORT=8000
```

Swagger UI at http://localhost:8000/docs.

### MCP server

```bash
python run_mcp.py                        # stdio (default for MCP clients)
WEBDOWN_TRANSPORT=http python run_mcp.py   # HTTP on port 8002
```

Configure via `.env`:

```bash
WEBDOWN_TRANSPORT=http
WEBDOWN_HOST=127.0.0.1
WEBDOWN_PORT=8002
```

### Pi integration

A pi extension auto-discovers MCP tools. Start the MCP server with HTTP transport, then load pi. The extension lives at `.pi/extensions/webdown.ts`.

See [docs/MCP.md](docs/MCP.md) for details.

### Streamlit UI

```bash
python run_streamlit.py
```

Three tabs: Sitemap Explorer, Full Site Scraper, Single Page Scraper.

## Project Structure

```
webdown/
  core/
    domain/
      entities/           → pure dataclasses (MarkdownFile, SitemapUrl, FeedItem, …)
      interfaces/         → ABCs (PageRenderer, MarkdownJobRepository, …)
    application/
      dto/                → data transfer objects
      use_cases/          → interactors (ExploreSitemap, StartAllPagesJob, …)
  infrastructure/
    database/             → schema initialization
    repositories/         → SQLite implementations
      mappers/            → row-to-entity mappers
    services/             → Playwright, BeautifulSoup, feedparser, requests
      consent_handlers/   → Cookie consent Chain of Responsibility
  presentation/
    api/
      adapters/           → FastAPI background processor
      models/             → Pydantic request/response models
      presenters/         → DTO-to-model converters
      routes/             → thin FastAPI route handlers
    mcp/
      server.py           → FastMCP server
      tools/              → MCP tool implementations
    streamlit/
      app.py              → Streamlit web UI
  startup/                → composition root
    api.py, mcp.py        → entry points
    app_factory.py        → FastAPI app factory
    repository_factory.py → repository wiring
    service_factory.py    → service wiring
    use_case_factory.py   → use case wiring
  main.py                 → thin re-export (backwards compat)
run_api.py, run_mcp.py, run_streamlit.py  → root-level entry points
.env.example              → environment configuration template
```

## Development

```bash
# Format & lint
black webdown/ tests/
ruff check webdown/ tests/

# Run tests
pytest

# Install dev dependencies
pip install -r requirements.txt
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **Web Index API**: http://localhost:8000/web-index/docs
- **Web Convert API**: http://localhost:8000/web-convert/docs
- **RSS API**: http://localhost:8000/rss/docs

Full endpoint reference in [docs/API.md](docs/API.md).

## Further Reading

- [Architecture Guide](docs/ARCHITECTURE.md) — layers, patterns, dependency rules
- [API Reference](docs/API.md) — endpoint specifications
- [MCP Server](docs/MCP.md) — tools, transport, pi integration
- [Development Guide](docs/DEVELOPMENT.md) — setup, testing, code style
