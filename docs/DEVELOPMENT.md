# Development Guide

## Setup

```bash
# Create virtual environment (Python 3.12+)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Copy environment config
cp .env.example .env
```

## Running

```bash
python run_api.py            # API server on port 8000
python run_mcp.py            # MCP server (stdio or HTTP)
python run_streamlit.py      # Streamlit UI
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_application_use_cases.py

# With coverage
pytest --cov=webdown
```

### Test Organization

```
tests/
├── conftest.py                          # shared fixtures, fake modules
├── test_api_characterization.py         # FastAPI endpoint tests
├── test_application_use_cases.py        # use case unit tests
└── test_infrastructure_repositories.py  # SQLite repository integration tests
```

Tests use an isolated temporary database directory via `DB_DIR` env var.
Optional dependencies (gitingest, feedparser) are faked when not installed.

## Code Quality

```bash
# Format
black webdown/ tests/

# Lint
ruff check webdown/ tests/

# Auto-fix lint issues
ruff check webdown/ tests/ --fix
```

## Project Conventions

### One class per file

Every class, interface, DTO, and entity lives in its own file. Exceptions:
`__init__.py` files and helper functions tightly coupled to a single class.

### Type hints

Use Python 3.12+ syntax: `str | None`, `list[Foo]`, not `Optional[str]` or `List[Foo]`.

### Imports

Always use absolute imports from `webdown`:

```python
from webdown.core.domain.entities.markdown_file import MarkdownFile
from webdown.startup.use_case_factory import create_explore_sitemap_use_case
```

### Layer rules

- `core/domain/` — no framework imports, no infrastructure, no presentation
- `core/application/` — depends only on `core/domain/`
- `infrastructure/` — depends only on `core/domain/`
- `presentation/` — depends on `core/application/`, `core/domain/`, and adapters from `infrastructure/`
- `startup/` — wires everything, can import from any layer

### Method size

Methods should stay under ~50 lines. Extract larger methods into private step methods
following the Pipeline/Extract Method pattern.

### Dependency injection

All dependencies are passed through the constructor. No service locators, no global
state, no singletons. Factories in `startup/` handle wiring.

## Adding a Feature

Follow this sequence:

1. Define domain entities in `core/domain/entities/`
2. Define domain interfaces in `core/domain/interfaces/`
3. Define DTOs in `core/application/dto/`
4. Create use case in `core/application/use_cases/`
5. Implement infrastructure in `infrastructure/`
6. Wire in `startup/` factories
7. Expose in `presentation/api/routes/` and/or `presentation/mcp/tools/`
8. Add tests

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8000` | API server port |
| `API_RELOAD` | `false` | Enable uvicorn reload |
| `WEBDOWN_TRANSPORT` | `stdio` | MCP transport (`stdio` / `http`) |
| `WEBDOWN_HOST` | `127.0.0.1` | MCP HTTP host |
| `WEBDOWN_PORT` | `8002` | MCP HTTP port |
| `WEBDOWN_MCP_URL` | `http://127.0.0.1:8002/mcp` | MCP URL for pi extension |
| `DB_DIR` | `./data` | SQLite database directory |
