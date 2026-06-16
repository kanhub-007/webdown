"""Tests for SaveMarkdownToFileUseCase (markdown file export).

Classical school: real use case + in-memory writer/repo fakes. Asserts on the
returned FileExportResult and that large content is NEVER in the response (only
path + size). Covers specs/2026-06-16_markdown-file-export/02-scenarios.md.
"""

from datetime import datetime, timezone

import pytest

from webdown.core.application.dto.save_markdown_to_file_request import SaveMarkdownToFileRequest
from webdown.core.application.use_cases.save_markdown_to_file import SaveMarkdownToFileUseCase
from webdown.core.domain.entities.markdown_file import MarkdownFile
from webdown.core.domain.exceptions import MarkdownFileNotFoundError
from tests.test_application._fakes import InMemoryMarkdownFileRepository


def _markdown_file(job_id: str, content: str) -> MarkdownFile:
    return MarkdownFile(
        job_id=job_id,
        content=content,
        created_at=datetime.now(timezone.utc).isoformat(),
        ip_address="mcp",
        file_size=len(content.encode("utf-8")),
        generation_time_seconds=0.1,
        base_url="https://example.com",
    )


class _RecordingWriter:
    """In-memory writer that stores what it was asked to write."""

    def __init__(self) -> None:
        self.written: dict[str, str] = {}

    def write(self, path: str, content: str):  # returns FileExportResult
        from pathlib import Path

        from webdown.core.domain.entities.file_export_result import FileExportResult

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.written[path] = content
        return FileExportResult(path=path, size_bytes=len(content.encode("utf-8")), pages_written=1)

    def write_many(self, dir_path: str, pages: dict[str, str]):
        raise NotImplementedError


def test_save_to_default_path_returns_path_and_size_not_content(tmp_path) -> None:
    """S1: default path used; result carries path+size, never content."""
    file_repo = InMemoryMarkdownFileRepository()
    file_repo.save_markdown_file(_markdown_file("J", "# Title\n\nbody"))
    writer = _RecordingWriter()
    use_case = SaveMarkdownToFileUseCase(file_repo, writer, output_dir=tmp_path)

    result = use_case.execute(SaveMarkdownToFileRequest(job_id="J"))

    assert result.path.endswith("J.md")
    assert result.size_bytes == len("# Title\n\nbody".encode("utf-8"))
    assert "# Title" in writer.written[result.path]      # actually written
    # The result itself exposes no content field:
    assert not hasattr(result, "content")


def test_save_to_explicit_output_path(tmp_path) -> None:
    """S2: explicit path is used verbatim; parent dir created."""
    file_repo = InMemoryMarkdownFileRepository()
    file_repo.save_markdown_file(_markdown_file("J", "# Hi"))
    writer = _RecordingWriter()
    use_case = SaveMarkdownToFileUseCase(file_repo, writer, output_dir=tmp_path)

    target = tmp_path / "nested" / "site.md"
    result = use_case.execute(SaveMarkdownToFileRequest(job_id="J", output_path=str(target)))

    assert result.path == str(target)
    assert (tmp_path / "nested").is_dir()


def test_job_not_found_raises(tmp_path) -> None:
    """S3: missing job -> MarkdownFileNotFoundError naming the job id; no file written."""
    writer = _RecordingWriter()
    use_case = SaveMarkdownToFileUseCase(InMemoryMarkdownFileRepository(), writer, output_dir=tmp_path)

    with pytest.raises(MarkdownFileNotFoundError, match="MISSING"):
        use_case.execute(SaveMarkdownToFileRequest(job_id="MISSING"))

    assert writer.written == {}


def test_empty_or_whitespace_job_id_is_invalid(tmp_path) -> None:
    """Input validation: blank job_id -> ValueError (distinct from not-found)."""
    use_case = SaveMarkdownToFileUseCase(
        InMemoryMarkdownFileRepository(), _RecordingWriter(), output_dir=tmp_path
    )
    with pytest.raises(ValueError):
        use_case.execute(SaveMarkdownToFileRequest(job_id="   "))


def test_split_per_page_not_yet_supported_raises_not_implemented(tmp_path) -> None:
    """S5: split_per_page is Slice 2; until then it must refuse cleanly (no wrong splits)."""
    file_repo = InMemoryMarkdownFileRepository()
    file_repo.save_markdown_file(_markdown_file("J", "# Hi"))
    use_case = SaveMarkdownToFileUseCase(file_repo, _RecordingWriter(), output_dir=tmp_path)

    with pytest.raises(NotImplementedError):
        use_case.execute(SaveMarkdownToFileRequest(job_id="J", split_per_page=True))


def test_default_path_uses_output_dir_and_job_id(tmp_path) -> None:
    """Default path is {output_dir}/{job_id}.md (co-located with data/)."""
    file_repo = InMemoryMarkdownFileRepository()
    file_repo.save_markdown_file(_markdown_file("job-xyz", "# X"))
    writer = _RecordingWriter()
    use_case = SaveMarkdownToFileUseCase(file_repo, writer, output_dir=tmp_path)

    result = use_case.execute(SaveMarkdownToFileRequest(job_id="job-xyz"))

    assert result.path == str(tmp_path / "job-xyz.md")


def test_real_filesystem_writer_writes_and_overwrites_disk(tmp_path) -> None:
    """The real FileSystemMarkdownFileWriter writes UTF-8 to disk and can overwrite."""
    from webdown.infrastructure.services.file_system_markdown_file_writer import (
        FileSystemMarkdownFileWriter,
    )

    file_repo = InMemoryMarkdownFileRepository()
    file_repo.save_markdown_file(_markdown_file("J", "# Hi\n\ncafé ☕"))  # multi-byte UTF-8
    writer = FileSystemMarkdownFileWriter()
    use_case = SaveMarkdownToFileUseCase(file_repo, writer, output_dir=tmp_path)

    first = use_case.execute(SaveMarkdownToFileRequest(job_id="J"))
    # size reflects UTF-8 bytes, not chars:
    assert first.size_bytes == len("# Hi\n\ncafé ☕".encode("utf-8"))
    assert (tmp_path / "J.md").read_text(encoding="utf-8") == "# Hi\n\ncafé ☕"

    # Overwrite default True: a second save succeeds and is reflected on disk.
    file_repo.save_markdown_file(_markdown_file("J", "# Replaced"))
    second = use_case.execute(SaveMarkdownToFileRequest(job_id="J"))
    assert (tmp_path / "J.md").read_text(encoding="utf-8") == "# Replaced"
    assert second.size_bytes == len("# Replaced".encode("utf-8"))


def test_split_per_page_writes_one_file_per_page(tmp_path) -> None:
    """S5 (Slice 2): split_per_page writes one .md per page from stored per-page markdown."""
    from webdown.core.domain.entities.page_conversion_status import PageConversionStatus
    from webdown.infrastructure.services.file_system_markdown_file_writer import (
        FileSystemMarkdownFileWriter,
    )
    from tests.test_application._fakes import InMemoryPageErrorRepository

    page_error_repo = InMemoryPageErrorRepository()
    page_error_repo.save_many("J", [
        PageConversionStatus(url="https://x.com/p/a", status="success", markdown="# A\n\nbody a"),
        PageConversionStatus(url="https://x.com/p/b", status="failed", error="boom"),
        PageConversionStatus(url="https://x.com/p/c", status="success", markdown="# C\n\nbody c"),
    ])
    use_case = SaveMarkdownToFileUseCase(
        InMemoryMarkdownFileRepository(),
        FileSystemMarkdownFileWriter(),
        output_dir=tmp_path,
        page_error_repository=page_error_repo,
    )

    out_dir = tmp_path / "site"
    result = use_case.execute(
        SaveMarkdownToFileRequest(job_id="J", output_path=str(out_dir), split_per_page=True)
    )

    assert result.pages_written == 2
    written = {p.name: p.read_text(encoding="utf-8") for p in out_dir.glob("*.md")}
    assert set(written) == {"a.md", "c.md"}
    assert "body a" in written["a.md"]
    assert "body c" in written["c.md"]


def test_split_per_page_without_per_page_repo_raises_not_implemented(tmp_path) -> None:
    """split_per_page with no per-page storage wired must refuse cleanly."""
    file_repo = InMemoryMarkdownFileRepository()
    file_repo.save_markdown_file(_markdown_file("J", "# Hi"))
    use_case = SaveMarkdownToFileUseCase(file_repo, _RecordingWriter(), output_dir=tmp_path)

    with pytest.raises(NotImplementedError):
        use_case.execute(SaveMarkdownToFileRequest(job_id="J", split_per_page=True))
