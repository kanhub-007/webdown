"""Use case for listing generated markdown file metadata."""

from webdown.core.application.dto.markdown_file_metadata_result import MarkdownFileMetadataResult
from webdown.core.domain.interfaces.markdown_file_repository import MarkdownFileRepository


class ListMarkdownFilesUseCase:
    """Lists generated markdown file metadata."""

    def __init__(self, file_repository: MarkdownFileRepository) -> None:
        """Initialize with the markdown file repository."""
        self._file_repository = file_repository

    def execute(self, limit: int = 100, offset: int = 0) -> list[MarkdownFileMetadataResult]:
        """List generated markdown file metadata.

        Args:
            limit: Maximum number of files to return (default 100).
            offset: Number of files to skip for pagination.
        """
        return [
            MarkdownFileMetadataResult(
                id=file.id,
                job_id=file.job_id,
                created_at=file.created_at,
                ip_address=file.ip_address,
                file_size=file.file_size,
                generation_time_seconds=file.generation_time_seconds,
                status=file.status,
                base_url=file.base_url,
            )
            for file in self._file_repository.list_markdown_files(limit=limit, offset=offset)
        ]
