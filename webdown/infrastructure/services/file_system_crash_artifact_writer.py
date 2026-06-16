"""Filesystem implementation of the crash artifact writer."""

from pathlib import Path
from urllib.parse import urlparse

from webdown.core.domain.interfaces.crash_artifact_writer import CrashArtifactWriter


def _slug(url: str) -> str:
    """Derive a filesystem-safe slug from a URL (last path segment)."""
    path = urlparse(url).path.strip("/")
    tail = path.split("/")[-1] if path else "page"
    return tail.replace(":", "_") or "page"


class FileSystemCrashArtifactWriter(CrashArtifactWriter):
    """Writes crash artifacts to data/debug/{job_id}/{slug}.{html,log}."""

    def __init__(self, debug_dir: Path) -> None:
        self._debug_dir = debug_dir

    def write(self, job_id: str, url: str, html: str, traceback_text: str) -> str:
        """Write HTML + traceback; return the HTML artifact path."""
        job_dir = self._debug_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        slug = _slug(url)
        html_path = job_dir / f"{slug}.html"
        log_path = job_dir / f"{slug}.log"
        html_path.write_bytes(html.encode("utf-8", errors="replace"))
        log_path.write_bytes(traceback_text.encode("utf-8", errors="replace"))
        return str(html_path)
