"""Use case for retrieving a generated markdown file."""

from webdown.core.domain.entities.markdown_file import MarkdownFile
from webdown.core.domain.interfaces.markdown_file_repository import MarkdownFileRepository


class GetMarkdownFileUseCase:
    """Retrieves a generated markdown file by job ID."""

    def __init__(self, file_repository: MarkdownFileRepository) -> None:
        """Initialize with the markdown file repository."""
        self._file_repository = file_repository

    def execute(self, job_id: str) -> MarkdownFile | None:
        """Get a generated markdown file by job ID."""
        return self._file_repository.get_markdown_file(job_id)
