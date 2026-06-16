"""Application DTO for all-pages markdown generation request."""

from dataclasses import dataclass


@dataclass
class GenerateAllPagesRequest:
    """Request data for generating markdown from all website pages."""

    base_url: str
    max_pages: int | None = None
    whitelist_patterns: list[str] | None = None
    blacklist_patterns: list[str] | None = None
    resume: bool = False
    capture_artifacts: bool = False
