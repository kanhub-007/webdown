"""Use case for exporting a stored markdown conversion to a .md file on disk.

Delivers large conversions as a file reference (path + size) instead of pushing
the full content through the tool response. Reads existing stored content only —
no re-rendering. See specs/2026-06-16_markdown-file-export/.
"""

import logging
from pathlib import Path

from webdown.core.application.dto.save_markdown_to_file_request import SaveMarkdownToFileRequest
from webdown.core.domain.entities.file_export_result import FileExportResult
from webdown.core.domain.exceptions import MarkdownFileNotFoundError
from webdown.core.domain.interfaces.markdown_file_repository import MarkdownFileRepository
from webdown.core.domain.interfaces.markdown_file_writer import MarkdownFileWriter
from webdown.core.domain.interfaces.page_error_repository import PageErrorRepository

logger = logging.getLogger(__name__)


class SaveMarkdownToFileUseCase:
    """Writes a stored markdown conversion to disk and returns a path reference."""

    def __init__(
        self,
        file_repository: MarkdownFileRepository,
        writer: MarkdownFileWriter,
        output_dir: Path,
        page_error_repository: PageErrorRepository | None = None,
    ) -> None:
        self._file_repository = file_repository
        self._writer = writer
        self._output_dir = output_dir
        self._page_error_repository = page_error_repository

    def execute(self, request: SaveMarkdownToFileRequest) -> FileExportResult:
        """Resolve path, read stored content, delegate write, return a reference."""
        if not request.job_id or not request.job_id.strip():
            raise ValueError("job_id is required")

        if request.split_per_page:
            return self._export_split(request)

        markdown_file = self._file_repository.get_markdown_file(request.job_id)
        if markdown_file is None or not markdown_file.content:
            raise MarkdownFileNotFoundError(request.job_id)

        path = self._resolve_path(request)
        self._check_overwrite(path, request.overwrite)
        try:
            return self._writer.write(path, markdown_file.content)
        except OSError as exc:
            raise ValueError(f"Cannot write to {path}: {exc}") from exc

    def _export_split(self, request: SaveMarkdownToFileRequest) -> FileExportResult:
        """Write one .md per successful page using stored per-page markdown."""
        if self._page_error_repository is None:
            raise NotImplementedError(
                "split_per_page requires per-page storage (page_error_repository)."
            )
        pages = self._page_error_repository.get_successful_markdown(request.job_id)
        if not pages:
            raise MarkdownFileNotFoundError(request.job_id)
        dir_path = self._resolve_split_dir(request)
        self._check_overwrite(dir_path, request.overwrite)
        try:
            return self._writer.write_many(dir_path, pages)
        except OSError as exc:
            raise ValueError(f"Cannot write to {dir_path}: {exc}") from exc

    @staticmethod
    def _check_overwrite(path: str, overwrite: bool) -> None:
        """Raise FileExistsError when overwrite is False and path exists."""
        target = Path(path)
        if not overwrite and target.exists():
            if target.is_dir():
                raise FileExistsError(
                    f"Directory already exists and overwrite=False: {path}"
                )
            raise FileExistsError(
                f"File already exists and overwrite=False: {path}"
            )

    def _resolve_path(self, request: SaveMarkdownToFileRequest) -> str:
        """Resolve the combined output path: explicit file/dir, else default."""
        if request.output_path:
            target = Path(request.output_path)
            if target.is_dir():
                return str(target / f"{request.job_id}.md")
            return str(target)
        return str(self._output_dir / f"{request.job_id}.md")

    def _resolve_split_dir(self, request: SaveMarkdownToFileRequest) -> str:
        """Resolve the split export directory: explicit, else default per-job dir."""
        if request.output_path:
            return request.output_path
        return str(self._output_dir / request.job_id)
