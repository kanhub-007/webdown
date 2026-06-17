"""Application DTO for generated markdown file metadata."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarkdownFileMetadataResult:
    """Result returned when listing markdown file metadata without content."""

    job_id: str
    created_at: datetime
    ip_address: str
    file_size: int
    generation_time_seconds: float
    base_url: str
    status: str = "completed"
    id: int | None = None
