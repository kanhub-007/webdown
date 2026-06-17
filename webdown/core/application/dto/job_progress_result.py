"""Application DTO for markdown generation progress result."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class JobProgressResult:
    """Result returned when querying markdown generation job progress."""

    job_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    total_pages: int | None = None
    processed_pages: int = 0
    error_message: str | None = None
    failed_pages: int = 0
    total_available: int | None = None
    truncated: bool | None = None
