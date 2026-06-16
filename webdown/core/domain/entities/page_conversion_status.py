"""Domain entity for a single page's conversion outcome.

Captured once per page during a bulk conversion. A success carries the page's
markdown (so per-page export and resume can read it back without re-converting);
a failure carries the error message (and optionally a path to a saved crash
artifact for debugging).
"""

from dataclasses import dataclass


@dataclass
class PageConversionStatus:
    """Represents the outcome of converting one page within a bulk job."""

    url: str
    status: str  # "success" | "failed"
    markdown: str | None = None
    error: str | None = None
    artifact_path: str | None = None
