"""SQLite implementation of markdown job repository."""

from datetime import datetime, timezone

from webdown.core.domain.entities.markdown_job import MarkdownJob
from webdown.core.domain.interfaces.markdown_job_repository import MarkdownJobRepository
from webdown.infrastructure.repositories.mappers.markdown_job_mapper import markdown_job_from_row
from webdown.infrastructure.repositories.sqlite_connection_factory import SqliteConnectionFactory


def _now_iso() -> str:
    """Return the current UTC datetime as an ISO string."""
    return datetime.now(timezone.utc).isoformat()


class SqliteMarkdownJobRepository(MarkdownJobRepository):
    """Stores markdown generation job progress in SQLite."""

    def __init__(self, connection_factory: SqliteConnectionFactory) -> None:
        """Initialize with a SQLite connection factory."""
        self._connection_factory = connection_factory

    def create_job(self, job_id: str, total_pages: int) -> None:
        """Create a new markdown generation job."""
        now = _now_iso()
        with self._connection_factory.get_connection("markdown_storage.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO job_progress (job_id, status, total_pages, processed_pages, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (job_id, "processing", total_pages, 0, now, now),
            )
            conn.commit()

    def update_job_progress(
        self,
        job_id: str,
        processed_pages: int,
        status: str = "processing",
        error_message: str | None = None,
        total_pages: int | None = None,
    ) -> None:
        """Update progress for an existing markdown generation job."""
        now = _now_iso()
        with self._connection_factory.get_connection("markdown_storage.db") as conn:
            cursor = conn.cursor()
            if total_pages is not None:
                cursor.execute(
                    """
                    UPDATE job_progress
                    SET processed_pages = ?, status = ?, updated_at = ?, error_message = ?, total_pages = ?
                    WHERE job_id = ?
                    """,
                    (processed_pages, status, now, error_message, total_pages, job_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE job_progress
                    SET processed_pages = ?, status = ?, updated_at = ?, error_message = ?
                    WHERE job_id = ?
                    """,
                    (processed_pages, status, now, error_message, job_id),
                )
            conn.commit()

    def get_job_progress(self, job_id: str) -> MarkdownJob | None:
        """Get progress for a markdown generation job."""
        with self._connection_factory.get_connection("markdown_storage.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT job_id, status, total_pages, processed_pages, created_at, updated_at, error_message
                FROM job_progress
                WHERE job_id = ?
                """,
                (job_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return markdown_job_from_row(row)
