"""Mapper functions for markdown job repository rows."""

from sqlite3 import Row

from webdown.core.domain.entities.markdown_job import MarkdownJob


def markdown_job_from_row(row: Row) -> MarkdownJob:
    """Map a SQLite row to a markdown job domain entity."""
    return MarkdownJob(
        job_id=row["job_id"],
        status=row["status"],
        total_pages=row["total_pages"],
        processed_pages=row["processed_pages"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        error_message=row["error_message"],
    )
