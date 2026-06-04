"""Markdown job progress tracking endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request

from webdown.core.application.use_cases.get_job_progress import GetJobProgressUseCase
from webdown.presentation.api.models import ProgressResponse
from webdown.presentation.api.presenters.progress_presenter import ProgressPresenter

router = APIRouter(prefix="/api/markdown/progress", tags=["Progress Tracking"])


def get_job_progress_use_case(request: Request) -> GetJobProgressUseCase:
    return request.app.state.get_job_progress_use_case


def get_progress_presenter() -> ProgressPresenter:
    return ProgressPresenter()


@router.get("/{job_id}", response_model=ProgressResponse)
async def track_progress(
    job_id: str,
    use_case: GetJobProgressUseCase = Depends(get_job_progress_use_case),
    presenter: ProgressPresenter = Depends(get_progress_presenter),
):
    """Track the progress of a markdown generation job.

    Poll this after starting a conversion to see how many pages have been
    processed, the overall status (processing/completed/failed), and any errors.
    Use the progress_percent field to show a progress bar to users.
    """
    result = use_case.execute(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return presenter.to_response(result)
