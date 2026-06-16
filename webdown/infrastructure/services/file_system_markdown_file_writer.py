"""Filesystem implementation of the markdown file writer."""

import logging
from pathlib import Path

from webdown.core.domain.entities.file_export_result import FileExportResult
from webdown.core.domain.interfaces.markdown_file_writer import MarkdownFileWriter

logger = logging.getLogger(__name__)


class FileSystemMarkdownFileWriter(MarkdownFileWriter):
    """Writes markdown documents to the local filesystem."""

    def write(self, path: str, content: str) -> FileExportResult:
        """Write a single markdown document; create parent dirs; overwrite by default."""
        target = Path(path)
        if target.exists():
            logger.warning("Overwriting existing markdown export at %s", target)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Write exact bytes (no platform newline translation) so size matches
        # len(content.encode('utf-8')) and LF line endings are preserved.
        data = content.encode("utf-8")
        target.write_bytes(data)
        return FileExportResult(path=str(target), size_bytes=len(data), pages_written=1)

    def write_many(self, dir_path: str, pages: dict[str, str]) -> FileExportResult:
        """Write one .md file per entry into a directory; return the aggregate result."""
        target_dir = Path(dir_path)
        target_dir.mkdir(parents=True, exist_ok=True)
        total_bytes = 0
        for name, content in pages.items():
            file_path = target_dir / f"{_safe_filename(name)}.md"
            data = content.encode("utf-8")
            file_path.write_bytes(data)
            total_bytes += len(data)
        return FileExportResult(path=str(target_dir), size_bytes=total_bytes, pages_written=len(pages))


def _safe_filename(name: str) -> str:
    """Reduce a URL/slug to a filesystem-safe filename stem."""
    # Drop the scheme/host if it looks like a URL; keep the trailing path segment.
    tail = name.rstrip("/").split("/")[-1]
    tail = tail.replace(":", "_")
    return tail or "page"
