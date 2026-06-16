"""Service factory functions."""

from functools import lru_cache

from webdown.infrastructure.services.beautifulsoup_html_to_markdown_converter import (
    BeautifulSoupHtmlToMarkdownConverter,
)
from webdown.infrastructure.services.ddgs_web_search_service import DDGSWebSearchService
from webdown.infrastructure.services.feedparser_rss_feed_aggregator import FeedparserRssFeedAggregator
from webdown.infrastructure.services.gitingest_github_repository_processor import GitingestGitHubRepositoryProcessor
from webdown.infrastructure.services.playwright_page_renderer import PlaywrightPageRenderer
from webdown.infrastructure.services.requests_sitemap_discovery_service import RequestsSitemapDiscoveryService
from webdown.infrastructure.services.requests_site_metadata_service import RequestsSiteMetadataService


@lru_cache(maxsize=1)
def create_sitemap_discovery_service() -> RequestsSitemapDiscoveryService:
    """Create the sitemap discovery service."""
    return RequestsSitemapDiscoveryService()


@lru_cache(maxsize=1)
def create_site_metadata_service() -> RequestsSiteMetadataService:
    """Create the site metadata service."""
    return RequestsSiteMetadataService()


@lru_cache(maxsize=1)
def create_page_renderer() -> PlaywrightPageRenderer:
    """Create the page renderer service."""
    return PlaywrightPageRenderer()


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
