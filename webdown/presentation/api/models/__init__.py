"""Presentation API models."""

from webdown.presentation.api.models.aggregated_rss_response import AggregatedRssResponse
from webdown.presentation.api.models.generate_all_pages_request import GenerateAllPagesRequest
from webdown.presentation.api.models.generate_github_repo_request import GenerateGitHubRepoRequest
from webdown.presentation.api.models.generate_single_page_request import GenerateSinglePageRequest
from webdown.presentation.api.models.job_response import JobResponse
from webdown.presentation.api.models.markdown_file_metadata import MarkdownFileMetadata
from webdown.presentation.api.models.progress_response import ProgressResponse
from webdown.presentation.api.models.rss_feed_item import RssFeedItem
from webdown.presentation.api.models.sitemap_request import SitemapRequest
from webdown.presentation.api.models.sitemap_response import SitemapResponse
from webdown.presentation.api.models.sitemap_url_info import SitemapUrlInfo

__all__ = [
    "AggregatedRssResponse",
    "GenerateAllPagesRequest",
    "GenerateGitHubRepoRequest",
    "GenerateSinglePageRequest",
    "JobResponse",
    "MarkdownFileMetadata",
    "ProgressResponse",
    "RssFeedItem",
    "SitemapRequest",
    "SitemapResponse",
    "SitemapUrlInfo",
]
