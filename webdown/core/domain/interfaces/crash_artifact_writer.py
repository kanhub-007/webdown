"""Domain interface for writing crash artifacts (debug HTML + traceback).

On a converter exception during bulk conversion, the offending HTML and the
full traceback are persisted so the failure can be reproduced and triaged.
"""

from abc import ABC, abstractmethod


class CrashArtifactWriter(ABC):
    """Persists crash artifacts (HTML + traceback) for failed conversions."""

    @abstractmethod
    def write(self, job_id: str, url: str, html: str, traceback_text: str) -> str:
        """Write the offending HTML + traceback; return the HTML artifact path."""
