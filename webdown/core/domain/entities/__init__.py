"""Domain entities."""

from webdown.core.domain.entities.feed_item import FeedItem
from webdown.core.domain.entities.markdown_file import MarkdownFile
from webdown.core.domain.entities.markdown_file_metadata import MarkdownFileMetadata
from webdown.core.domain.entities.markdown_job import MarkdownJob
from webdown.core.domain.entities.search_result import SearchResult
from webdown.core.domain.entities.sitemap_url import SitemapUrl
from webdown.core.domain.entities.website_pages import WebsitePages

__all__ = [
    "FeedItem",
    "MarkdownFile",
    "MarkdownFileMetadata",
    "MarkdownJob",
    "SearchResult",
    "SitemapUrl",
    "WebsitePages",
]
