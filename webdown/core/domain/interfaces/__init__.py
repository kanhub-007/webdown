"""Domain interfaces."""

from webdown.core.domain.interfaces.background_processor import BackgroundProcessor
from webdown.core.domain.interfaces.github_repository_processor import GitHubRepositoryProcessor
from webdown.core.domain.interfaces.html_to_markdown_converter import HtmlToMarkdownConverter
from webdown.core.domain.interfaces.markdown_file_repository import MarkdownFileRepository
from webdown.core.domain.interfaces.markdown_job_repository import MarkdownJobRepository
from webdown.core.domain.interfaces.page_renderer import PageRenderer
from webdown.core.domain.interfaces.rss_feed_aggregator import RssFeedAggregator
from webdown.core.domain.interfaces.sitemap_discovery_service import SitemapDiscoveryService
from webdown.core.domain.interfaces.site_metadata_service import SiteMetadataService

__all__ = [
    "BackgroundProcessor",
    "GitHubRepositoryProcessor",
    "HtmlToMarkdownConverter",
    "MarkdownFileRepository",
    "MarkdownJobRepository",
    "PageRenderer",
    "RssFeedAggregator",
    "SitemapDiscoveryService",
    "SiteMetadataService",
]
