"""Domain-layer exceptions."""


class SearchServiceError(Exception):
    """Raised when the web search service is unavailable or fails."""


class MarkdownFileNotFoundError(Exception):
    """Raised when a requested markdown conversion does not exist or is not completed."""

    def __init__(self, job_id: str) -> None:
        """Store the job id and build a descriptive message."""
        self.job_id = job_id
        super().__init__(f"No completed markdown file found for job_id={job_id!r}")
