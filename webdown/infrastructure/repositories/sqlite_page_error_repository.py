"""SQLite implementation of the page-error (per-page conversion status) repository."""

from urllib.parse import urlparse

from webdown.core.domain.entities.page_conversion_status import PageConversionStatus
from webdown.core.domain.interfaces.page_error_repository import PageErrorRepository
from webdown.infrastructure.repositories.mappers.page_conversion_status_mapper import (
    page_conversion_status_from_row,
)
from webdown.infrastructure.repositories.sqlite_connection_factory import SqliteConnectionFactory


def _normalize_host(url: str) -> str:
    """Return the hostname of a URL, ignoring a leading 'www.'."""
    host = urlparse(url).hostname or ""
    return host[4:] if host.startswith("www.") else host


class SqlitePageErrorRepository(PageErrorRepository):
    """Stores per-page conversion outcomes in SQLite."""

    def __init__(self, connection_factory: SqliteConnectionFactory) -> None:
        """Initialize with a SQLite connection factory."""
        self._connection_factory = connection_factory

    def save(self, job_id: str, status: PageConversionStatus) -> None:
        """Upsert one page outcome for a job."""
        with self._connection_factory.get_connection("markdown_storage.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO page_conversion_status (job_id, url, status, markdown, error, artifact_path)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id, url) DO UPDATE SET
                    status = excluded.status,
                    markdown = excluded.markdown,
                    error = excluded.error,
                    artifact_path = excluded.artifact_path
                """,
                (job_id, status.url, status.status, status.markdown, status.error, status.artifact_path),
            )
            conn.commit()

    def save_many(self, job_id: str, statuses: list[PageConversionStatus]) -> None:
        """Upsert many page outcomes for a job."""
        if not statuses:
            return
        rows = [
            (job_id, s.url, s.status, s.markdown, s.error or "(no message)", s.artifact_path)
            for s in statuses
        ]
        with self._connection_factory.get_connection("markdown_storage.db") as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT INTO page_conversion_status (job_id, url, status, markdown, error, artifact_path)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id, url) DO UPDATE SET
                    status = excluded.status,
                    markdown = excluded.markdown,
                    error = excluded.error,
                    artifact_path = excluded.artifact_path
                """,
                rows,
            )
            conn.commit()

    def get_by_job(self, job_id: str) -> list[PageConversionStatus]:
        """Return all recorded page outcomes for a job."""
        with self._connection_factory.get_connection("markdown_storage.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT url, status, markdown, error, artifact_path
                FROM page_conversion_status
                WHERE job_id = ?
                ORDER BY id
                """,
                (job_id,),
            )
            rows = cursor.fetchall()
        return [page_conversion_status_from_row(row) for row in rows]

    def get_successful_markdown(self, job_id: str) -> dict[str, str]:
        """Return {url: markdown} for the successful pages of a job."""
        with self._connection_factory.get_connection("markdown_storage.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT url, markdown
                FROM page_conversion_status
                WHERE job_id = ? AND status = 'success' AND markdown IS NOT NULL
                """,
                (job_id,),
            )
            rows = cursor.fetchall()
        return {row["url"]: row["markdown"] for row in rows}

    def succeeded_urls(self, base_url: str) -> set[str]:
        """Return URLs converted successfully for a base_url (host-normalized)."""
        target_host = _normalize_host(base_url)
        with self._connection_factory.get_connection("markdown_storage.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT url
                FROM page_conversion_status
                WHERE status = 'success'
                """,
            )
            rows = cursor.fetchall()
        return {row["url"] for row in rows if _normalize_host(row["url"]) == target_host}
