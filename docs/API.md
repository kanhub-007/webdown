# API Reference

## Endpoints

### Web Index API — `/web-index`

#### `POST /api/sitemap/explore`

Discover all pages from a website sitemap.

```bash
curl -X POST http://localhost:8000/web-index/api/sitemap/explore \
  -H "Content-Type: application/json" \
  -d '{"base_url": "https://example.com", "max_pages": 500}'
```

**Request:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `base_url` | string | required | Website URL |
| `max_pages` | int | 1000 | Maximum pages to discover |

**Response:**
```json
{
  "pages": [{"loc": "https://...", "lastmod": "2024-01-01"}],
  "total_count": 42,
  "sitemap_files_visited": ["https://example.com/sitemap.xml"]
}
```

---

### Web Convert API — `/web-convert`

#### `POST /api/markdown/generate-single`

Convert a single page to Markdown.

```bash
curl -X POST http://localhost:8000/web-convert/api/markdown/generate-single \
  -H "Content-Type: application/json" \
  -d '{"url": "https://docs.python.org/3/"}'
```

Returns `{"job_id": "...", "status": "processing", "message": "..."}`.

#### `POST /api/markdown/generate-all`

Convert all pages from a website sitemap to a single Markdown file.

```bash
curl -X POST http://localhost:8000/web-convert/api/markdown/generate-all \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://example.com",
    "max_pages": 100,
    "whitelist_patterns": ["docs/"],
    "blacklist_patterns": ["private/"]
  }'
```

#### `POST /api/markdown/generate-github-repo`

Convert a GitHub repository to Markdown.

```bash
curl -X POST http://localhost:8000/web-convert/api/markdown/generate-github-repo \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo"}'
```

#### `GET /api/markdown/progress/{job_id}`

Track a conversion job.

```json
{
  "job_id": "...",
  "status": "processing",
  "total_pages": 100,
  "processed_pages": 45,
  "progress_percent": 45.0,
  "created_at": "...",
  "updated_at": "...",
  "error_message": null
}
```

#### `GET /api/markdown/download/{job_id}`

Download generated Markdown (returns `text/markdown`).

#### `GET /api/markdown/list`

List all generated files (metadata only, no content).

#### `GET /api/markdown/metadata/{job_id}`

Get detailed metadata for a file including sitemap URLs.

---

### RSS API — `/rss`

#### `GET /api/rss/aggregate`

Aggregate RSS feeds from Bloomberg, ZeroHedge, Huggingface Blog, Google AI Blog, and MIT Technology Review.

```bash
curl http://localhost:8000/rss/api/rss/aggregate

# Filter by date
curl "http://localhost:8000/rss/api/rss/aggregate?published_after=2026-06-01T00:00:00Z"
```

**Response:**
```json
{
  "items": [
    {"title": "...", "link": "...", "published": "...", "summary": "...", "source": "Bloomberg"}
  ],
  "total": 30,
  "generated_at": "2026-06-04T12:00:00Z"
}
```

Results are cached for 5 minutes when no date filter is applied.

---

### Health — `/`

#### `GET /health`

```json
{"status": "healthy", "service": "WebDown API", "version": "1.0.0"}
```

#### `GET /`

Root endpoint with API links and documentation URLs.

## OpenAPI Documentation

Interactive docs available at:

- http://localhost:8000/docs — main Swagger UI
- http://localhost:8000/redoc — main ReDoc
- http://localhost:8000/web-index/docs — Web Index API
- http://localhost:8000/web-convert/docs — Web Convert API
- http://localhost:8000/rss/docs — RSS API
