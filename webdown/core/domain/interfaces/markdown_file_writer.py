"""Domain interface for writing exported markdown to a filesystem."""

from abc import ABC, abstractmethod

from webdown.core.domain.entities.file_export_result import FileExportResult


class MarkdownFileWriter(ABC):
    """Writes exported markdown content to disk (injectable for testing)."""

    @abstractmethod
    def write(self, path: str, content: str) -> FileExportResult:
        """Write a single markdown document to path; return the export result."""

    @abstractmethod
    def write_many(self, dir_path: str, pages: dict[str, str]) -> FileExportResult:
        """Write one file per {name: content} into a directory (split_per_page)."""
