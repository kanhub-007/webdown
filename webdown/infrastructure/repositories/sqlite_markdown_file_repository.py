"""SQLite implementation of markdown file repository."""

from webdown.core.domain.entities.markdown_file import MarkdownFile
from webdown.core.domain.entities.markdown_file_metadata import MarkdownFileMetadata
from webdown.core.domain.interfaces.markdown_file_repository import MarkdownFileRepository
from webdown.infrastructure.repositories.mappers.markdown_file_mapper import (
    markdown_file_from_row,
    markdown_file_metadata_from_row,
)
from webdown.infrastructure.repositories.sqlite_connection_factory import SqliteConnectionFactory


class SqliteMarkdownFileRepository(MarkdownFileRepository):
    """Stores generated markdown files and metadata in SQLite."""

    def __init__(self, connection_factory: SqliteConnectionFactory) -> None:
        """Initialize with a SQLite connection factory."""
        self._connection_factory = connection_factory

    def save_markdown_file(self, markdown_file: MarkdownFile) -> None:
        """Save generated markdown content and metadata."""
        if markdown_file.content is None:
            raise ValueError("Markdown content is required")

        with self._connection_factory.get_connection("markdown_storage.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO markdown_files (job_id, content, created_at, ip_address, file_size, generation_time_seconds, base_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    markdown_file.job_id,
                    markdown_file.content,
                    markdown_file.created_at.isoformat(),
                    markdown_file.ip_address,
                    markdown_file.file_size,
                    markdown_file.generation_time_seconds,
                    markdown_file.base_url,
                ),
            )
            cursor.executemany(
                """
                INSERT INTO sitemap_metadata (job_id, url, lastmod)
                VALUES (?, ?, ?)
                """,
                [(markdown_file.job_id, u.loc, u.lastmod) for u in markdown_file.sitemap_urls],
            )
            conn.commit()

    def get_markdown_file(self, job_id: str) -> MarkdownFile | None:
        """Retrieve a generated markdown file by job ID."""
        with self._connection_factory.get_connection("markdown_storage.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, job_id, content, created_at, ip_address, file_size, generation_time_seconds, status, base_url
                FROM markdown_files
                WHERE job_id = ?
                """,
                (job_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            cursor.execute(
                """
                SELECT url, lastmod
                FROM sitemap_metadata
                WHERE job_id = ?
                """,
                (job_id,),
            )
            sitemap_rows = cursor.fetchall()
        return markdown_file_from_row(row, sitemap_rows)

    def list_markdown_files(self, limit: int = 100, offset: int = 0) -> list[MarkdownFileMetadata]:
        """List generated markdown file metadata without content.

        Args:
            limit: Maximum number of rows to return (default 100).
            offset: Number of rows to skip for pagination.

        Returns:
            List of MarkdownFileMetadata, newest first.
        """
        with self._connection_factory.get_connection("markdown_storage.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, job_id, created_at, ip_address, file_size, generation_time_seconds, status, base_url
                FROM markdown_files
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """, (limit, offset))
            rows = cursor.fetchall()
        return [markdown_file_metadata_from_row(row) for row in rows]
