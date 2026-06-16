"""Mapper functions for page conversion status repository rows."""

from sqlite3 import Row

from webdown.core.domain.entities.page_conversion_status import PageConversionStatus


def page_conversion_status_from_row(row: Row) -> PageConversionStatus:
    """Map a SQLite row to a PageConversionStatus domain entity."""
    return PageConversionStatus(
        url=row["url"],
        status=row["status"],
        markdown=row["markdown"],
        error=row["error"],
        artifact_path=row["artifact_path"],
    )
