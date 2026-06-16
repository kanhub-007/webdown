"""Tests for application use cases."""

from datetime import datetime
from types import SimpleNamespace

from webdown.core.application.dto.generate_single_page_request import GenerateSinglePageRequest
from webdown.core.application.use_cases.aggregate_rss_feeds import AggregateRssFeedsUseCase
from webdown.core.application.use_cases.explore_sitemap import ExploreSitemapUseCase
from webdown.core.application.use_cases.get_job_progress import GetJobProgressUseCase
from webdown.core.application.use_cases.list_markdown_files import ListMarkdownFilesUseCase
from webdown.core.application.use_cases.start_all_pages_markdown_job import StartAllPagesMarkdownJobUseCase
from webdown.core.application.use_cases.start_github_repo_markdown_job import StartGitHubRepoMarkdownJobUseCase
from webdown.core.application.use_cases.start_single_page_markdown_job import StartSinglePageMarkdownJobUseCase
from webdown.core.application.dto.generate_all_pages_request import GenerateAllPagesRequest
from webdown.core.application.dto.generate_github_repo_request import GenerateGitHubRepoRequest
from webdown.core.application.dto.sitemap_explore_request import SitemapExploreRequest
from webdown.core.domain.entities.markdown_file_metadata import MarkdownFileMetadata
from webdown.core.domain.entities.sitemap_url import SitemapUrl


def test_start_single_page_markdown_job() -> None:
    """Single-page job starter creates progress record synchronously and returns JobResult."""
    created_jobs: list[tuple[str, int]] = []
    submissions: list[tuple[object, tuple[object, ...], dict[str, object]]] = []

    def execute_generation(job_id: str, url: str, ip_address: str) -> None:
        """Represent background execution."""

    job_repo = SimpleNamespace(create_job=lambda job_id, total_pages: created_jobs.append((job_id, total_pages)))
    generation_use_case = SimpleNamespace(execute=execute_generation)
    bg = SimpleNamespace(submit=lambda task, *args, **kwargs: submissions.append((task, args, kwargs)) or "")
    use_case = StartSinglePageMarkdownJobUseCase(job_repo, generation_use_case)

    result = use_case.execute(
        request=GenerateSinglePageRequest(url="https://example.com"),
        ip_address="127.0.0.1",
        background_processor=bg,
    )

    assert result.job_id is not None
    assert result.status == "processing"
    assert created_jobs == [(result.job_id, 1)]
    assert len(submissions) == 1
    assert submissions[0][0] is generation_use_case.execute
    assert submissions[0][1] == (result.job_id, "https://example.com", "127.0.0.1")


def test_start_all_pages_markdown_job() -> None:
    """All-pages job starter creates job with 0 total_pages and passes DTO fields through."""
    created_jobs: list[tuple[str, int]] = []
    submissions: list[tuple[object, tuple[object, ...], dict[str, object]]] = []

    def execute_generation(
        job_id: str,
        base_url: str,
        max_pages: int,
        whitelist: list[str] | None,
        blacklist: list[str] | None,
        ip: str,
        resume: bool = False,
        capture_artifacts: bool = False,
    ) -> None:
        """Represent background execution."""

    job_repo = SimpleNamespace(create_job=lambda job_id, total_pages: created_jobs.append((job_id, total_pages)))
    generation_use_case = SimpleNamespace(execute=execute_generation)
    bg = SimpleNamespace(submit=lambda task, *args, **kwargs: submissions.append((task, args, kwargs)) or "")
    use_case = StartAllPagesMarkdownJobUseCase(job_repo, generation_use_case)

    result = use_case.execute(
        request=GenerateAllPagesRequest(base_url="https://example.com", max_pages=5, whitelist_patterns=["docs"]),
        ip_address="10.0.0.1",
        background_processor=bg,
    )

    assert result.job_id is not None
    assert created_jobs == [(result.job_id, 0)]
    assert len(submissions) == 1
    assert submissions[0][1] == (result.job_id, "https://example.com", 5, ["docs"], None, "10.0.0.1", False, False)


def test_start_github_repo_markdown_job() -> None:
    """GitHub repo job starter creates job and passes repo_url through."""
    created_jobs: list[tuple[str, int]] = []
    submissions: list[tuple[object, tuple[object, ...], dict[str, object]]] = []

    def execute_generation(job_id: str, repo_url: str, ip_address: str) -> None:
        """Represent background execution."""

    job_repo = SimpleNamespace(create_job=lambda job_id, total_pages: created_jobs.append((job_id, total_pages)))
    generation_use_case = SimpleNamespace(execute=execute_generation)
    bg = SimpleNamespace(submit=lambda task, *args, **kwargs: submissions.append((task, args, kwargs)) or "")
    use_case = StartGitHubRepoMarkdownJobUseCase(job_repo, generation_use_case)

    result = use_case.execute(
        request=GenerateGitHubRepoRequest(repo_url="https://github.com/user/repo"),
        ip_address="127.0.0.1",
        background_processor=bg,
    )

    assert result.job_id is not None
    assert created_jobs == [(result.job_id, 1)]
    assert submissions[0][1] == (result.job_id, "https://github.com/user/repo", "127.0.0.1")


def test_get_job_progress_returns_dto() -> None:
    """GetJobProgressUseCase maps domain entity to DTO."""
    job_repo = SimpleNamespace(
        get_job_progress=lambda job_id: SimpleNamespace(
            job_id="job-1",
            status="completed",
            total_pages=5,
            processed_pages=5,
            created_at="2024-01-01",
            updated_at="2024-01-02",
            error_message=None,
            failed_pages=0,
            total_available=None,
            truncated=None,
        )
    )
    use_case = GetJobProgressUseCase(job_repo)
    result = use_case.execute("job-1")
    assert result is not None
    assert result.job_id == "job-1"
    assert result.status == "completed"
    assert result.total_pages == 5
    assert result.processed_pages == 5


def test_get_job_progress_returns_none_for_missing() -> None:
    """GetJobProgressUseCase returns None when job does not exist."""
    use_case = GetJobProgressUseCase(SimpleNamespace(get_job_progress=lambda job_id: None))
    assert use_case.execute("nonexistent") is None


def test_list_markdown_files_returns_dtos() -> None:
    """ListMarkdownFilesUseCase maps domain entities to DTOs."""
    file_repo = SimpleNamespace(
        list_markdown_files=lambda: [
            MarkdownFileMetadata(
                id=1,
                job_id="a",
                created_at="2024-01-01",
                ip_address="127.0.0.1",
                file_size=100,
                generation_time_seconds=1.0,
                status="completed",
                base_url="https://a.com",
            ),
            MarkdownFileMetadata(
                id=2,
                job_id="b",
                created_at="2024-01-02",
                ip_address="127.0.0.2",
                file_size=200,
                generation_time_seconds=2.0,
                status="completed",
                base_url="https://b.com",
            ),
        ]
    )
    use_case = ListMarkdownFilesUseCase(file_repo)
    result = use_case.execute()
    assert len(result) == 2
    assert result[0].job_id == "a"
    assert result[1].job_id == "b"


def test_explore_sitemap_returns_dto() -> None:
    """ExploreSitemapUseCase maps domain entity to DTO."""
    service = SimpleNamespace(
        discover_website_pages=lambda base_url, max_pages=None: SimpleNamespace(
            pages=[SitemapUrl(loc="https://example.com/docs", lastmod="2024-01-01")],
            sitemap_files_visited=["https://example.com/sitemap.xml"],
            total_available=1,
            truncated=False,
        )
    )
    use_case = ExploreSitemapUseCase(service)
    result = use_case.execute(SitemapExploreRequest(base_url="https://example.com"))
    assert len(result.pages) == 1
    assert result.pages[0].loc == "https://example.com/docs"
    assert result.sitemap_files_visited == ["https://example.com/sitemap.xml"]


def test_aggregate_rss_feeds_delegates() -> None:
    """AggregateRssFeedsUseCase delegates to the aggregator service."""
    import asyncio

    async def fake_aggregate(published_after: datetime | None = None) -> list[SimpleNamespace]:
        return [SimpleNamespace(title="T", link="L", source="S", published=None, summary=None)]

    use_case = AggregateRssFeedsUseCase(SimpleNamespace(aggregate_all=fake_aggregate))
    result = asyncio.run(use_case.execute())
    assert len(result) == 1
    assert result[0].title == "T"
