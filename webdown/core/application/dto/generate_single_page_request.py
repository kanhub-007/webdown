"""Application DTO for single-page markdown generation request."""

from dataclasses import dataclass


@dataclass
class GenerateSinglePageRequest:
    """Request data for generating markdown from a single page."""

    url: str
