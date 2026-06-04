"""API response model for markdown generation progress."""

from pydantic import BaseModel, Field


class ProgressResponse(BaseModel):
    """Response model for job progress tracking."""

    job_id: str = Field(description="Unique job identifier")
    status: str = Field(description="Current status: processing, completed, or failed")
    total_pages: int | None = Field(default=None, description="Total number of pages in the job")
    processed_pages: int | None = Field(default=None, description="Number of pages processed so far")
    progress_percent: float | None = Field(default=None, description="Progress percentage (0-100)")
    created_at: str = Field(description="ISO timestamp when the job was created")
    updated_at: str = Field(description="ISO timestamp when the job was last updated")
    error_message: str | None = Field(default=None, description="Error details if status is failed")
