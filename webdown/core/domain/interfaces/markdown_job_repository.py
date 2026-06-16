"""Domain repository interface for markdown job progress."""

from abc import ABC, abstractmethod

from webdown.core.domain.entities.markdown_job import MarkdownJob


class MarkdownJobRepository(ABC):
    """Persists markdown generation job progress."""

    @abstractmethod
    def create_job(self, job_id: str, total_pages: int) -> None:
        """Create a new markdown generation job."""

    @abstractmethod
    def update_job_progress(
        self,
        job_id: str,
        processed_pages: int,
        status: str = "processing",
        error_message: str | None = None,
        total_pages: int | None = None,
        failed_pages: int | None = None,
        total_available: int | None = None,
        truncated: bool | None = None,
    ) -> None:
        """Update progress for an existing markdown generation job."""

    @abstractmethod
    def get_job_progress(self, job_id: str) -> MarkdownJob | None:
        """Get progress for a markdown generation job."""
