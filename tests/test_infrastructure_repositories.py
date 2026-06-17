"""Tests for SQLite repository implementations."""

from datetime import datetime, timezone
from pathlib import Path

from webdown.core.domain.entities.markdown_file import MarkdownFile
from webdown.core.domain.entities.sitemap_url import SitemapUrl
from webdown.infrastructure.database.sqlite_schema_initializer import SqliteSchemaInitializer
from webdown.infrastructure.repositories.sqlite_connection_factory import SqliteConnectionFactory
from webdown.infrastructure.repositories.sqlite_markdown_file_repository import SqliteMarkdownFileRepository
from webdown.infrastructure.repositories.sqlite_markdown_job_repository import SqliteMarkdownJobRepository


def test_sqlite_markdown_repositories_store_progress_and_files(tmp_path: Path) -> None:
    """Markdown repositories persist job progress, generated content, and sitemap metadata."""
    connection_factory = SqliteConnectionFactory(str(tmp_path))
    SqliteSchemaInitializer(connection_factory).initialize_markdown_storage()
    job_repository = SqliteMarkdownJobRepository(connection_factory)
    file_repository = SqliteMarkdownFileRepository(connection_factory)

    job_repository.create_job("job-1", 2)
    job_repository.update_job_progress("job-1", 1, total_pages=2)
    progress = job_repository.get_job_progress("job-1")

    assert progress is not None
    assert progress.job_id == "job-1"
    assert progress.status == "processing"
    assert progress.total_pages == 2
    assert progress.processed_pages == 1

    file_repository.save_markdown_file(
        MarkdownFile(
            job_id="job-1",
            content="# Content",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            ip_address="127.0.0.1",
            file_size=9,
            generation_time_seconds=1.5,
            base_url="https://example.com",
            sitemap_urls=[SitemapUrl(loc="https://example.com/docs", lastmod="2024-01-01")],
        )
    )

    markdown_file = file_repository.get_markdown_file("job-1")
    assert markdown_file is not None
    assert markdown_file.content == "# Content"
    assert markdown_file.sitemap_urls == [SitemapUrl(loc="https://example.com/docs", lastmod="2024-01-01")]

    files = file_repository.list_markdown_files()
    assert len(files) == 1
    assert files[0].job_id == "job-1"
    assert files[0].base_url == "https://example.com"
