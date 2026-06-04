"""Presenter for job response endpoints."""

from webdown.core.application.dto.job_result import JobResult
from webdown.presentation.api.models import JobResponse


class JobPresenter:
    """Converts job DTOs to Pydantic API response models."""

    def to_response(self, result: JobResult) -> JobResponse:
        """Convert a job result to the Pydantic response model."""
        return JobResponse(
            job_id=result.job_id,
            status=result.status,
            message=result.message,
        )
