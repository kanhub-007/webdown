"""API response model for background job creation."""

from pydantic import BaseModel, Field


class JobResponse(BaseModel):
    """Response model for job creation."""

    job_id: str = Field(description="Unique job identifier — use this to track progress and download results")
    status: str = Field(description="Job status: processing, completed, or failed")
    message: str = Field(description="Human-readable status message")
