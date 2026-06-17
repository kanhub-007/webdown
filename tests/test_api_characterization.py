"""Characterization tests for the current FastAPI API surface."""

from datetime import datetime, timezone
from types import SimpleNamespace


def test_health_and_root_endpoints(app_client: tuple[object, object]) -> None:
    """Health and root endpoints expose the current service metadata."""
    client, _main_module = app_client

    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json() == {
        "status": "healthy",
        "service": "WebDown API",
        "version": "1.0.0",
    }

    root_response = client.get("/")
    assert root_response.status_code == 200
    root_payload = root_response.json()
    assert root_payload["message"] == "Welcome to the Website Documentation Tools API"
    assert root_payload["version"] == "1.0.0"
    assert set(root_payload["apis"]) == {"web_index", "web_convert", "rss"}


def test_sitemap_explore_endpoint_uses_discovery_service(
    app_client: tuple[object, object],
) -> None:
    """The sitemap endpoint returns discovered page URLs and visited sitemaps."""
    client, main_module = app_client

    def fake_explore_sitemap(request: object = None) -> SimpleNamespace:
        assert request is not None
        assert request.base_url == "https://example.com/"
        assert request.max_pages == 10
        return SimpleNamespace(
            pages=[SimpleNamespace(loc="https://example.com/docs", lastmod="2024-01-01")],
            sitemap_files_visited=["https://example.com/sitemap.xml"],
            total_available=1,
            truncated=False,
        )

    main_module.web_index_api.state.explore_sitemap_use_case = SimpleNamespace(execute=fake_explore_sitemap)

    response = client.post(
        "/web-index/api/sitemap/explore",
        json={"base_url": "https://example.com", "max_pages": 10},
    )

    assert response.status_code == 200
    assert response.json() == {
        "pages": [{"loc": "https://example.com/docs", "lastmod": "2024-01-01"}],
        "total_count": 1,
        "sitemap_files_visited": ["https://example.com/sitemap.xml"],
        "total_available": 1,
        "truncated": False,
    }


def test_markdown_generate_all_endpoint_schedules_background_work(
    app_client: tuple[object, object],
) -> None:
    """The generate-all endpoint creates a job response without running scraping work."""
    client, main_module = app_client
    executed_requests: list[dict[str, object]] = []
    scheduled_tasks: list[tuple[object, tuple[object, ...], dict[str, object]]] = []

    def fake_task() -> None:
        scheduled_tasks.append((fake_task, (), {}))

    def fake_execute(**kwargs: object) -> SimpleNamespace:
        bg = kwargs.get("background_processor")
        executed_requests.append(kwargs)
        if bg:
            bg.submit(fake_task)
        return SimpleNamespace(
            job_id="job-1",
            status="processing",
            message="Markdown generation started. Use the job_id to track progress.",
        )

    main_module.web_convert_api.state.start_all_pages_markdown_job_use_case = SimpleNamespace(execute=fake_execute)
    response = client.post(
        "/web-convert/api/markdown/generate-all",
        json={
            "base_url": "https://example.com",
            "max_pages": 5,
            "whitelist_patterns": ["docs"],
            "blacklist_patterns": ["private"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "processing"
    assert payload["message"] == "Markdown generation started. Use the job_id to track progress."
    assert payload["job_id"] == "job-1"
    assert len(executed_requests) == 1
    assert executed_requests[0]["request"].base_url == "https://example.com/"
    assert executed_requests[0]["request"].max_pages == 5
    assert len(scheduled_tasks) == 1
    assert scheduled_tasks[0][0] is fake_task


def test_progress_endpoint_returns_calculated_percent(
    app_client: tuple[object, object],
) -> None:
    """The progress endpoint converts stored job progress to the API response shape."""
    client, main_module = app_client

    def fake_get_job_progress(job_id: str) -> SimpleNamespace:
        assert job_id == "job-1"
        return SimpleNamespace(
            job_id="job-1",
            status="processing",
            total_pages=10,
            processed_pages=4,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:01:00",
            error_message=None,
            failed_pages=0,
            total_available=None,
            truncated=None,
        )

    main_module.web_convert_api.state.get_job_progress_use_case = SimpleNamespace(execute=fake_get_job_progress)

    response = client.get("/web-convert/api/markdown/progress/job-1")

    assert response.status_code == 200
    assert response.json() == {
        "job_id": "job-1",
        "status": "processing",
        "total_pages": 10,
        "processed_pages": 4,
        "progress_percent": 40.0,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:01:00",
        "error_message": None,
        "failed_pages": 0,
        "total_available": None,
        "truncated": None,
    }


def test_rss_endpoint_maps_aggregated_items(
    app_client: tuple[object, object],
) -> None:
    """The RSS endpoint maps aggregator items to the public response model."""
    client, main_module = app_client
    published = datetime(2024, 1, 1, tzinfo=timezone.utc)

    async def fake_aggregate_all(published_after: datetime | None = None) -> list[SimpleNamespace]:
        assert published_after is None
        return [
            SimpleNamespace(
                title="Example Article",
                link="https://example.com/article",
                published=published,
                summary="A summary",
                source="Example Feed",
            )
        ]

    main_module.rss_api.state.aggregate_rss_feeds_use_case = SimpleNamespace(execute=fake_aggregate_all)

    response = client.get("/rss/api/rss/aggregate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"] == [
        {
            "title": "Example Article",
            "link": "https://example.com/article",
            "published": "2024-01-01T00:00:00Z",
            "summary": "A summary",
            "source": "Example Feed",
        }
    ]
    assert "generated_at" in payload
