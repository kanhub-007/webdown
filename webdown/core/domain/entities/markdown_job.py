"""Domain entity for a markdown generation job."""

from dataclasses import dataclass


@dataclass
class MarkdownJob:
    """Represents progress and status for a markdown generation job."""

    job_id: str
    status: str
    created_at: str
    updated_at: str
    total_pages: int | None = None
    processed_pages: int = 0
    error_message: str | None = None
    # Resilience / fidelity fields (backwards-compatible defaults):
    failed_pages: int = 0
    total_available: int | None = None
    truncated: bool | None = None
