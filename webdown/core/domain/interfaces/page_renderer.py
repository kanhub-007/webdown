"""Domain service interface for web page rendering."""

from abc import ABC, abstractmethod
from collections.abc import Callable


class PageRenderer(ABC):
    """Renders web pages to HTML."""

    @abstractmethod
    def render(self, url: str) -> str | None:
        """Render one URL to HTML."""

    @abstractmethod
    def render_all(
        self,
        urls: list[str],
        progress_callback: Callable[[int], None] | None = None,
    ) -> dict[str, str | None]:
        """Render multiple URLs to HTML."""
