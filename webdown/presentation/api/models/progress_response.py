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
    failed_pages: int = Field(default=0, description="Number of pages that failed conversion")
    total_available: int | None = Field(default=None, description="Total pages in sitemap (before any cap)")
    truncated: bool | None = Field(default=None, description="True if results were capped by max_pages")
