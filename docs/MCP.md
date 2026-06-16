# MCP Server

WebDown exposes all functionality as MCP tools via FastMCP.

## Quick Start

```bash
# stdio transport (default for MCP clients like Claude Desktop, Cursor)
python run_mcp.py

# HTTP transport (for pi extension, remote clients)
WEBDOWN_TRANSPORT=http python run_mcp.py
```

The HTTP server runs on `http://127.0.0.1:8002/mcp` by default.

Configure via `.env`:

```bash
WEBDOWN_TRANSPORT=http
WEBDOWN_HOST=127.0.0.1
WEBDOWN_PORT=8002
```

## Tools

### Sitemap

| Tool | Description |
|------|-------------|
| `search_web(query, max_results=20)` | Search the web and return URLs + snippets |
| `explore_sitemap(base_url, max_pages=100)` | Discover all pages from a website sitemap |

### RSS

| Tool | Description |
|------|-------------|
| `aggregate_rss_feeds(published_after=None)` | Aggregate crypto/AI news feeds |

### Markdown

| Tool | Description |
|------|-------------|
| `convert_single_page(url)` | Convert one page to Markdown (synchronous) |
| `convert_all_pages(base_url, max_pages=100, whitelist, blacklist)` | Convert entire website (synchronous, blocks until done) |
| `convert_github_repo(repo_url)` | Convert a GitHub repository (synchronous) |
| `get_job_progress(job_id)` | Check conversion progress |
| `download_markdown(job_id)` | Get generated Markdown content |
| `list_markdown_files()` | List all generated files (metadata only) |
| `generate_job_id()` | Generate a unique tracking ID |

### Example Calls

```
search_web("python async best practices", max_results=5)
explore_sitemap("https://docs.python.org", max_pages=50)
convert_single_page("https://example.com/about")
get_job_progress("550e8400-e29b-41d4-a716-446655440000")
download_markdown("550e8400-e29b-41d4-a716-446655440000")
aggregate_rss_feeds("2026-06-01T00:00:00Z")
```

## Pi Integration

A pi extension at `.pi/extensions/webdown.ts` auto-discovers all MCP tools
when pi starts.

**Setup:**

1. Start the MCP server with HTTP transport: `WEBDOWN_TRANSPORT=http python run_mcp.py`
2. Start pi — the extension connects and registers all tools
3. Call tools natively: `explore_sitemap("https://example.com")`

The extension reads `WEBDOWN_MCP_URL` env var (defaults to `http://127.0.0.1:8002/mcp`).

## Architecture

```
run_mcp.py
  → webdown/startup/mcp.py    (composition root)
    → bootstrap()                 (initialize SQLite)
    → create_server()             (FastMCP + tools)
      → webdown/presentation/mcp/server.py
        → tools/search.py         (register_search_tools)
        → tools/sitemap.py        (register_sitemap_tools)
        → tools/rss.py            (register_rss_tools)
        → tools/markdown.py       (register_markdown_tools)
```

MCP tools are thin adapters — each calls a use case via the use case factory,
converts the result to a dict, and returns it. No infrastructure imports.
