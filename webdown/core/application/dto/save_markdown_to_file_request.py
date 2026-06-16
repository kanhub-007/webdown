"""Application DTO for save-markdown-to-file requests."""

from dataclasses import dataclass


@dataclass
class SaveMarkdownToFileRequest:
    """Request to export a stored markdown conversion to a .md file."""

    job_id: str
    output_path: str | None = None
    split_per_page: bool = False
    overwrite: bool = True
