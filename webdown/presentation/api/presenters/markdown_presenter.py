"""Presenter for markdown-related endpoints."""

from webdown.core.application.dto.markdown_file_metadata_result import MarkdownFileMetadataResult
from webdown.presentation.api.models import MarkdownFileMetadata


class MarkdownPresenter:
    """Converts markdown DTOs to Pydantic API response models."""

    def metadata_to_response(self, metadata: MarkdownFileMetadataResult) -> dict[str, object]:
        """Convert markdown file metadata result to a JSON-compatible dict."""
        return {
            "id": metadata.id,
            "job_id": metadata.job_id,
            "created_at": metadata.created_at,
            "ip_address": metadata.ip_address,
            "file_size": metadata.file_size,
            "generation_time_seconds": metadata.generation_time_seconds,
            "status": metadata.status,
            "base_url": metadata.base_url,
        }

    def metadata_list_to_response(self, metadata_list: list[MarkdownFileMetadataResult]) -> dict[str, object]:
        """Convert a list of metadata results to a JSON response."""
        return {
            "files": [self.metadata_to_response(item) for item in metadata_list],
            "total": len(metadata_list),
        }

    def to_pydantic_metadata(
        self,
        metadata: MarkdownFileMetadataResult,
        sitemap_urls: list[dict[str, str | None]],
    ) -> MarkdownFileMetadata:
        """Convert a metadata result to the full Pydantic response model."""
        return MarkdownFileMetadata(
            job_id=metadata.job_id,
            created_at=metadata.created_at,
            ip_address=metadata.ip_address,
            file_size=metadata.file_size,
            generation_time_seconds=metadata.generation_time_seconds,
            base_url=metadata.base_url,
            sitemap_url_count=len(sitemap_urls),
            sitemap_urls=sitemap_urls,
        )
