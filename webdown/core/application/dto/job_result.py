"""Application DTO for background job creation result."""

from dataclasses import dataclass


@dataclass
class JobResult:
    """Result returned after starting a background markdown generation job."""

    job_id: str
    status: str = "processing"
    message: str = "Markdown generation started. Use the job_id to track progress."
