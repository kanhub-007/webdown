"""Use case for retrieving markdown job progress."""

from webdown.core.application.dto.job_progress_result import JobProgressResult
from webdown.core.domain.interfaces.markdown_job_repository import MarkdownJobRepository


class GetJobProgressUseCase:
    """Retrieves progress for a markdown generation job."""

    def __init__(self, job_repository: MarkdownJobRepository) -> None:
        """Initialize with the job repository."""
        self._job_repository = job_repository

    def execute(self, job_id: str) -> JobProgressResult | None:
        """Get progress for a job ID."""
        job = self._job_repository.get_job_progress(job_id)
        if job is None:
            return None
        return JobProgressResult(
            job_id=job.job_id,
            status=job.status,
            total_pages=job.total_pages,
            processed_pages=job.processed_pages,
            created_at=job.created_at,
            updated_at=job.updated_at,
            error_message=job.error_message,
            failed_pages=job.failed_pages,
            total_available=job.total_available,
            truncated=job.truncated,
        )
