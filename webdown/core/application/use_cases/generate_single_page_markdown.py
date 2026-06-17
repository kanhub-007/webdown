"""Use case for generating markdown from a single web page."""

import logging
import time
from datetime import datetime, timezone

from webdown.core.domain.entities.markdown_file import MarkdownFile
from webdown.core.domain.entities.sitemap_url import SitemapUrl
from webdown.core.domain.interfaces.html_to_markdown_converter import HtmlToMarkdownConverter
from webdown.core.domain.interfaces.markdown_file_repository import MarkdownFileRepository
from webdown.core.domain.interfaces.markdown_job_repository import MarkdownJobRepository
from webdown.core.domain.interfaces.page_renderer import PageRenderer

logger = logging.getLogger(__name__)


class GenerateSinglePageMarkdownUseCase:
    """Generates Markdown for one rendered web page."""

    def __init__(
        self,
        job_repository: MarkdownJobRepository,
        file_repository: MarkdownFileRepository,
        page_renderer: PageRenderer,
        html_to_markdown_converter: HtmlToMarkdownConverter,
    ) -> None:
        """Initialize the use case with its dependencies."""
        self._job_repository = job_repository
        self._file_repository = file_repository
        self._page_renderer = page_renderer
        self._html_to_markdown_converter = html_to_markdown_converter

    def execute(self, job_id: str, url: str, ip_address: str) -> None:
        """Generate Markdown for a single web page."""
        start_time = time.time()

        try:
            html = self._page_renderer.render(url)
            if not html:
                raise RuntimeError(f"Failed to render page: {url}")

            markdown = self._html_to_markdown_converter.convert(html, url)
            if not markdown or not markdown.strip():
                raise RuntimeError("Conversion resulted in empty markdown content")

            self._file_repository.save_markdown_file(
                MarkdownFile(
                    job_id=job_id,
                    content=markdown,
                    created_at=datetime.now(timezone.utc),
                    ip_address=ip_address,
                    file_size=len(markdown.encode("utf-8")),
                    generation_time_seconds=time.time() - start_time,
                    base_url=url,
                    sitemap_urls=[SitemapUrl(loc=url)],
                )
            )
            self._job_repository.update_job_progress(job_id, 1, "completed")
        except Exception as error:
            logger.error(f"Error generating markdown for {url}: {error}", exc_info=True)
            self._job_repository.update_job_progress(job_id, 0, "failed", str(error))
