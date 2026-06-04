# WebDown — High-Fidelity Website to Markdown

**Convert any website to clean, structured Markdown — with real browser rendering, intelligent table handling, smart cookie consent navigation, and built-in RSS feed aggregation from crypto & AI news sources.**

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT">
  <img src="https://img.shields.io/badge/interfaces-REST%20%7C%20MCP%20%7C%20Streamlit-purple" alt="Interfaces">
</p>

---

## Why WebDown?

Most HTML-to-Markdown tools do a poor job on real-world documentation sites. They fail on tables, get confused by cookie walls, miss JavaScript-rendered content, and produce inconsistent heading structures. Worse, none of them also aggregate RSS feeds from your favorite news sources. **WebDown is different.**

### 🎯 What Makes It Better

| Problem | Typical Tools | WebDown |
|---------|-------------|---------|
| **Tables** | Strip them, flatten them, or output raw HTML | Converts to clean **pipe tables** using pandas — handles `rowspan`, `colspan`, ARIA `div[role="table"]`, and missing `<thead>` |
| **Cookie consent walls** | Return an empty consent page | **Chain of Responsibility** with 3 handlers — detects modals, overlays, and Yahoo-style scroll consent; retries up to 5 times; checks iframes |
| **JavaScript-rendered content** | Only see the loading spinner | Renders every page with **headless Playwright** — full browser, waits for network idle, scrolls to load lazy content |
| **Heading duplication** | Page title and H1 both appear | **Breadcrumb-aware** heading normalization — detects when the H1 mirrors the breadcrumb title and adjusts levels accordingly |
| **Code blocks** | Lose language metadata, flatten nested code | Extracts `lang-*` classes, marks inline vs. block code separately, strips `$Copy` buttons |
| **Alerts / callouts** | Ignore them or dump raw text | Detects 18 alert types (Note, Warning, Danger, Tip, etc.) and renders as clean **blockquotes with emoji headers** |
| **Scale** | Crashes or thrashes on 100+ pages | Concurrent rendering with configurable parallelism; **background job processing** with real-time progress tracking |
| **Architecture** | Monolithic scripts | Clean architecture — domain entities, use cases, repositories, dependency injection. Testable, maintainable, extensible. |

---

## Features

### Core Conversion

- ✅ **Custom HTML→Markdown engine** — purpose-built for documentation sites, not a generic converter
- ✅ **Table conversion** — pandas-powered: auto-detects header rows, handles merged cells, converts ARIA `div[role="table"]` to standard `<table>` first
- ✅ **Code block handling** — preserves language annotations, distinguishes inline vs. block code, strips clipboard-copy artifacts
- ✅ **Alert/admonition blocks** — recognizes 18 types (Note, Warning, Danger, Tip, Success, Example, FAQ, etc.) with emoji icons
- ✅ **Breadcrumb-based titles** — generates clean `# Path / To / Page` headers from URL structure
- ✅ **Smart heading normalization** — avoids duplicate H1s, adjusts heading levels when breadcrumbs are present
- ✅ **Special elements** — `<details>` as collapsible blockquotes, `<dl>` definition lists, `<figure>` with captions, standalone images

### Rendering

- ✅ **Playwright headless browser** — fully renders JavaScript, SPAs, and lazy-loaded content before extraction
- ✅ **Cookie consent navigation** — Chain of Responsibility: Yahoo scroll → selector click → overlay close, with iframe support and retry logic
- ✅ **GitBook support** — automatically detects GitBook sites and optimizes rendering
- ✅ **Lazy content loading** — scrolls to page bottom to trigger infinite scroll and deferred images
- ✅ **Concurrent rendering** — process multiple pages in parallel with configurable concurrency

### Delivery

| Feature | REST API | MCP Server | Streamlit UI |
|---------|----------|------------|-------------|
| Single page → Markdown | ✅ | ✅ | ✅ |
| Full site → Markdown | ✅ | ✅ | ✅ |
| GitHub repo → Markdown | ✅ | ✅ | — |
| Sitemap exploration | ✅ | ✅ | ✅ |
| Progress tracking | ✅ | ✅ | ✅ |
| Download / list files | ✅ | ✅ | ✅ |
| RSS aggregation | ✅ | ✅ | — |
| Whitelist/blacklist filtering | ✅ | ✅ | ✅ |

### Architecture

```
presentation/   → REST routes (FastAPI), MCP tools, Streamlit UI
startup/        → Composition root (factory wiring)
core/application/ → Use cases (orchestration), DTOs
core/domain/    → Entities, interfaces (pure logic)
infrastructure/ → SQLite repos, Playwright, BeautifulSoup, feedparser, gitingest
```

All dependencies point inward. The domain layer knows nothing about frameworks. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for design patterns and dependency rules.

---

## Quick Start

### Prerequisites

- Python 3.12+
- Playwright browser binaries

```bash
# Clone
git clone https://github.com/kanhub-007/webdown.git
cd webdown

# Virtual environment
uv venv --python 3.12
uv sync --all-extras

# Install browser
.venv/Scripts/python -m playwright install chromium

# Or with pip
pip install -r requirements.txt
playwright install chromium
```

### Run

```bash
python run_api.py            # REST API → http://localhost:8000/docs
python run_mcp.py            # MCP Server → stdio
python run_streamlit.py      # Streamlit UI → http://localhost:8501
```

Or via Docker:

```bash
docker-compose up --build
```

### Example: Convert a docs site

```bash
# 1. Explore the sitemap
curl -X POST http://localhost:8000/web-index/api/sitemap/explore \
  -H "Content-Type: application/json" \
  -d '{"base_url": "https://docs.python.org/3/", "max_pages": 500}'

# 2. Convert all pages to a single Markdown file
curl -X POST http://localhost:8000/web-convert/api/markdown/generate-all \
  -H "Content-Type: application/json" \
  -d '{"base_url": "https://docs.python.org/3/", "max_pages": 100}'

# 3. Poll progress (use the job_id from step 2)
curl http://localhost:8000/web-convert/api/markdown/progress/{job_id}

# 4. Download the result
curl http://localhost:8000/web-convert/api/markdown/download/{job_id} > docs.md
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/web-index/api/sitemap/explore` | Discover all pages from a website sitemap |
| `POST` | `/web-convert/api/markdown/generate-single` | Convert a single page to Markdown |
| `POST` | `/web-convert/api/markdown/generate-all` | Convert all sitemap pages to Markdown |
| `POST` | `/web-convert/api/markdown/generate-github-repo` | Convert a GitHub repo to Markdown |
| `GET`  | `/web-convert/api/markdown/progress/{job_id}` | Track conversion progress |
| `GET`  | `/web-convert/api/markdown/download/{job_id}` | Download generated Markdown |
| `GET`  | `/web-convert/api/markdown/list` | List all generated files |
| `GET`  | `/web-convert/api/markdown/metadata/{job_id}` | Get file metadata |
| `GET`  | `/rss/api/rss/aggregate` | Aggregate RSS feeds |
| `GET`  | `/health` | Health check |

Swagger UI: http://localhost:8000/docs — full API reference in [docs/API.md](docs/API.md).

---

## MCP Tools

Integrate with any MCP-compatible client (Claude Desktop, Cursor, Windsurf, Pi):

| Tool | Description |
|------|-------------|
| `explore_sitemap` | Discover pages from a website sitemap |
| `convert_single_page` | Convert one URL to Markdown |
| `convert_all_pages` | Convert entire site to Markdown |
| `convert_github_repo` | Convert a GitHub repository to Markdown |
| `get_job_progress` | Check conversion job status |
| `download_markdown` | Download generated Markdown |
| `list_markdown_files` | List all generated files |
| `aggregate_rss_feeds` | Aggregate from 5 RSS feed sources |

HTTP transport available via `WEBDOWN_TRANSPORT=http`. Full MCP docs in [docs/MCP.md](docs/MCP.md).

---

## Project Structure

```
webdown/
  core/domain/entities/         → pure dataclasses
  core/domain/interfaces/       → ABCs (contracts)
  core/application/dto/         → data transfer objects
  core/application/use_cases/   → interactors (orchestration)
  infrastructure/database/      → SQLite schema
  infrastructure/repositories/  → SQLite implementations + mappers
  infrastructure/services/      → Playwright, BeautifulSoup, gitingest, feedparser
    consent_handlers/           → Chain of Responsibility for cookie consent
  presentation/api/             → FastAPI routes, Pydantic models, presenters
  presentation/mcp/             → FastMCP server + tools
  presentation/streamlit/       → Web UI
  startup/                      → Composition root (DI factories)
```

---

## Development

```bash
# Format & lint
black webdown/ tests/
ruff check webdown/ tests/

# Type check (via ruff)
ruff check webdown/ --select E,F,I,N,UP --fix

# Run tests
pytest
```

---

## Further Reading

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Clean architecture layers, design patterns, dependency rules
- [docs/API.md](docs/API.md) — Full endpoint reference with request/response schemas
- [docs/MCP.md](docs/MCP.md) — MCP server configuration, tools, transport modes
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) — Setup, testing, code conventions
