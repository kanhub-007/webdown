"""Use case for exporting a stored markdown conversion to a .md file on disk.

Delivers large conversions as a file reference (path + size) instead of pushing
the full content through the tool response. Reads existing stored content only —
no re-rendering. See specs/2026-06-16_markdown-file-export/.
"""

from pathlib import Path

from webdown.core.application.dto.save_markdown_to_file_request import SaveMarkdownToFileRequest
from webdown.core.domain.entities.file_export_result import FileExportResult
from webdown.core.domain.exceptions import MarkdownFileNotFoundError
from webdown.core.domain.interfaces.markdown_file_repository import MarkdownFileRepository
from webdown.core.domain.interfaces.markdown_file_writer import MarkdownFileWriter


class SaveMarkdownToFileUseCase:
    """Writes a stored markdown conversion to disk and returns a path reference."""

    def __init__(
        self,
        file_repository: MarkdownFileRepository,
        writer: MarkdownFileWriter,
        output_dir: Path,
    ) -> None:
        self._file_repository = file_repository
        self._writer = writer
        self._output_dir = output_dir

    def execute(self, request: SaveMarkdownToFileRequest) -> FileExportResult:
        """Resolve path, read stored content, delegate write, return a reference."""
        if not request.job_id or not request.job_id.strip():
            raise ValueError("job_id is required")

        markdown_file = self._file_repository.get_markdown_file(request.job_id)
        if markdown_file is None or not markdown_file.content:
            raise MarkdownFileNotFoundError(request.job_id)

        if request.split_per_page:
            # Slice 2: unblocked once per-page markdown is stored, but the combined
            # blob cannot be split safely on '---' (pages may contain rules).
            raise NotImplementedError(
                "split_per_page is not yet implemented; use the combined file."
            )

        path = self._resolve_path(request)
        return self._writer.write(path, markdown_file.content)

    def _resolve_path(self, request: SaveMarkdownToFileRequest) -> str:
        """Resolve the output path: explicit file/dir, else default under output_dir."""
        if request.output_path:
            target = Path(request.output_path)
            # If the caller pointed at a directory, append {job_id}.md.
            if target.is_dir():
                return str(target / f"{request.job_id}.md")
            return str(target)
        return str(self._output_dir / f"{request.job_id}.md")
