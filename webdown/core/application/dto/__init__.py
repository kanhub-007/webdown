"""Application DTOs (data transfer objects)."""

from webdown.core.application.dto.generate_all_pages_request import GenerateAllPagesRequest
from webdown.core.application.dto.generate_github_repo_request import GenerateGitHubRepoRequest
from webdown.core.application.dto.generate_single_page_request import GenerateSinglePageRequest
from webdown.core.application.dto.job_progress_result import JobProgressResult
from webdown.core.application.dto.job_result import JobResult
from webdown.core.application.dto.markdown_file_metadata_result import MarkdownFileMetadataResult
from webdown.core.application.dto.sitemap_explore_request import SitemapExploreRequest
from webdown.core.application.dto.sitemap_explore_result import SitemapExploreResult

__all__ = [
    "GenerateAllPagesRequest",
    "GenerateGitHubRepoRequest",
    "GenerateSinglePageRequest",
    "JobProgressResult",
    "JobResult",
    "MarkdownFileMetadataResult",
    "SitemapExploreRequest",
    "SitemapExploreResult",
]
