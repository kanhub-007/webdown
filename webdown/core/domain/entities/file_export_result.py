"""Domain value object for a markdown file export result."""

from dataclasses import dataclass


@dataclass
class FileExportResult:
    """Result of exporting a markdown conversion to disk.

    Carries only references (path, size), never the content — so large
    conversions cross boundaries cheaply.
    """

    path: str
    size_bytes: int
    pages_written: int | None = None
