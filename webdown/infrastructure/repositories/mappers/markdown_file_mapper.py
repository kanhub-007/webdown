"""Mapper functions for markdown file repository rows."""

from sqlite3 import Row

from webdown.core.domain.entities.markdown_file import MarkdownFile
from webdown.core.domain.entities.markdown_file_metadata import MarkdownFileMetadata
from webdown.core.domain.entities.sitemap_url import SitemapUrl


def markdown_file_from_row(row: Row, sitemap_rows: list[Row]) -> MarkdownFile:
    """Map SQLite rows to a markdown file domain entity."""
    return MarkdownFile(
        id=row["id"],
        job_id=row["job_id"],
        content=row["content"],
        created_at=row["created_at"],
        ip_address=row["ip_address"],
        file_size=row["file_size"],
        generation_time_seconds=row["generation_time_seconds"],
        status=row["status"],
        base_url=row["base_url"],
        sitemap_urls=[
            SitemapUrl(loc=sitemap_row["url"], lastmod=sitemap_row["lastmod"]) for sitemap_row in sitemap_rows
        ],
    )


def markdown_file_metadata_from_row(row: Row) -> MarkdownFileMetadata:
    """Map a SQLite row to a markdown file metadata domain entity."""
    return MarkdownFileMetadata(
        id=row["id"],
        job_id=row["job_id"],
        created_at=row["created_at"],
        ip_address=row["ip_address"],
        file_size=row["file_size"],
        generation_time_seconds=row["generation_time_seconds"],
        status=row["status"],
        base_url=row["base_url"],
    )
