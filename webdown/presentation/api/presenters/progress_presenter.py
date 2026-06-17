"""Presenter for progress-related endpoints."""

from webdown.core.application.dto.job_progress_result import JobProgressResult
from webdown.presentation.api.models import ProgressResponse


class ProgressPresenter:
    """Converts progress DTOs to Pydantic API response models."""

    def to_response(self, result: JobProgressResult) -> ProgressResponse:
        """Convert a job progress result to the Pydantic response model."""
        progress_percent = None
        if result.total_pages and result.total_pages > 0:
            progress_percent = (result.processed_pages / result.total_pages) * 100

        return ProgressResponse(
            job_id=result.job_id,
            status=result.status,
            total_pages=result.total_pages,
            processed_pages=result.processed_pages,
            progress_percent=progress_percent,
            created_at=result.created_at,
            updated_at=result.updated_at,
            error_message=result.error_message,
            failed_pages=result.failed_pages,
            total_available=result.total_available,
            truncated=result.truncated,
        )
