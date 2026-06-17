"""Service factory functions."""

from functools import lru_cache
from pathlib import Path

from webdown.infrastructure.services.beautifulsoup_html_to_markdown_converter import (
    BeautifulSoupHtmlToMarkdownConverter,
)
from webdown.infrastructure.services.ddgs_web_search_service import DDGSWebSearchService
from webdown.infrastructure.services.feedparser_rss_feed_aggregator import FeedparserRssFeedAggregator
from webdown.infrastructure.services.file_system_crash_artifact_writer import FileSystemCrashArtifactWriter
from webdown.infrastructure.services.file_system_markdown_file_writer import FileSystemMarkdownFileWriter
from webdown.infrastructure.services.gitingest_github_repository_processor import GitingestGitHubRepositoryProcessor
from webdown.infrastructure.services.playwright_page_renderer import PlaywrightPageRenderer
from webdown.infrastructure.services.requests_sitemap_discovery_service import RequestsSitemapDiscoveryService
from webdown.infrastructure.services.requests_site_metadata_service import RequestsSiteMetadataService
from webdown.infrastructure.services.retrying_page_renderer import RetryingPageRenderer


@lru_cache(maxsize=1)
def create_sitemap_discovery_service() -> RequestsSitemapDiscoveryService:
    """Create the sitemap discovery service."""
    return RequestsSitemapDiscoveryService()


@lru_cache(maxsize=1)
def create_site_metadata_service() -> RequestsSiteMetadataService:
    """Create the site metadata service."""
    return RequestsSiteMetadataService()


@lru_cache(maxsize=1)
def create_page_renderer() -> RetryingPageRenderer:
    """Create the page renderer service (wrapped with retry decorator).

    Sets the Windows Proactor event loop policy if needed — this must happen
    before any asyncio event loop is created (the renderer is the first consumer).
    """
    import asyncio
    import sys

    if sys.platform == "win32" and sys.version_info < (3, 14):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception:
            pass  # Already set or incompatible platform

    from webdown.infrastructure.services.playwright_page_renderer import build_consent_chain

    consent_handler = build_consent_chain()
    return RetryingPageRenderer(PlaywrightPageRenderer(consent_handler=consent_handler))


@lru_cache(maxsize=1)
def create_html_to_markdown_converter() -> BeautifulSoupHtmlToMarkdownConverter:
    """Create the HTML-to-Markdown converter service."""
    return BeautifulSoupHtmlToMarkdownConverter()


@lru_cache(maxsize=1)
def create_github_repository_processor() -> GitingestGitHubRepositoryProcessor:
    """Create the GitHub repository processor service."""
    return GitingestGitHubRepositoryProcessor()


@lru_cache(maxsize=1)
def create_rss_feed_aggregator() -> FeedparserRssFeedAggregator:
    """Create the RSS feed aggregator service."""
    return FeedparserRssFeedAggregator()


@lru_cache(maxsize=1)
def create_web_search_service() -> DDGSWebSearchService:
    """Create the web search service."""
    return DDGSWebSearchService()


@lru_cache(maxsize=1)
def create_markdown_file_writer() -> FileSystemMarkdownFileWriter:
    """Create the filesystem markdown export writer."""
    return FileSystemMarkdownFileWriter()


def create_crash_artifact_writer(debug_dir: Path) -> FileSystemCrashArtifactWriter:
    """Create the crash-artifact writer for a given debug directory."""
    return FileSystemCrashArtifactWriter(debug_dir)
