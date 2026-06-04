"""Domain service interface for converting HTML to Markdown."""

from abc import ABC, abstractmethod


class HtmlToMarkdownConverter(ABC):
    """Converts HTML content to Markdown."""

    @abstractmethod
    def convert(self, html: str, base_url: str) -> str:
        """Convert HTML content to Markdown."""
