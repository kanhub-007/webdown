"""Domain repository interface for generated markdown files."""

from abc import ABC, abstractmethod

from webdown.core.domain.entities.markdown_file import MarkdownFile
from webdown.core.domain.entities.markdown_file_metadata import MarkdownFileMetadata


class MarkdownFileRepository(ABC):
    """Persists generated markdown files and metadata."""

    @abstractmethod
    def save_markdown_file(self, markdown_file: MarkdownFile) -> None:
        """Save generated markdown content and metadata."""

    @abstractmethod
    def get_markdown_file(self, job_id: str) -> MarkdownFile | None:
        """Retrieve a generated markdown file by job ID."""

    @abstractmethod
    def list_markdown_files(self) -> list[MarkdownFileMetadata]:
        """List generated markdown file metadata without content."""
