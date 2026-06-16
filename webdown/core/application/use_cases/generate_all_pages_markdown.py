"""Use case for generating markdown from all sitemap-discovered pages.

Resilience behaviour: each page's conversion is an independent outcome. A page
that fails (empty render, empty markdown, or converter exception) is recorded
as a per-page failure and processing continues; the job only ends ``failed`` if
NO page succeeds, otherwise it ends ``completed_with_errors`` (partial) or
``completed`` (all success). Successful pages' markdown is stored individually
to enable per-page export and resume.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from webdown.core.domain.entities.markdown_file import MarkdownFile
from webdown.core.domain.entities.page_conversion_status import PageConversionStatus
from webdown.core.domain.entities.sitemap_url import SitemapUrl
from webdown.core.domain.interfaces.html_to_markdown_converter import HtmlToMarkdownConverter
from webdown.core.domain.interfaces.markdown_file_repository import MarkdownFileRepository
from webdown.core.domain.interfaces.markdown_job_repository import MarkdownJobRepository
from webdown.core.domain.interfaces.page_error_repository import PageErrorRepository
from webdown.core.domain.interfaces.page_renderer import PageRenderer
from webdown.core.domain.interfaces.sitemap_discovery_service import SitemapDiscoveryService

logger = logging.getLogger(__name__)


class GenerateAllPagesMarkdownUseCase:
    """Generates combined Markdown for all pages discovered from a website sitemap."""

    def __init__(
        self,
        job_repository: MarkdownJobRepository,
        file_repository: MarkdownFileRepository,
        sitemap_discovery_service: SitemapDiscoveryService,
        page_renderer: PageRenderer,
        html_to_markdown_converter: HtmlToMarkdownConverter,
        page_error_repository: PageErrorRepository,
    ) -> None:
        self._job_repository = job_repository
        self._file_repository = file_repository
        self._sitemap_discovery_service = sitemap_discovery_service
        self._page_renderer = page_renderer
        self._html_to_markdown_converter = html_to_markdown_converter
        self._page_error_repository = page_error_repository

    def execute(
        self,
        job_id: str,
        base_url: str,
        max_pages: int,
        whitelist_patterns: list[str] | None,
        blacklist_patterns: list[str] | None,
        ip_address: str,
        resume: bool = False,
    ) -> None:
        """Generate combined Markdown for sitemap-discovered pages.

        With resume=True, pages already converted successfully for this base_url
        are skipped (not re-rendered), and the combined output is regenerated
        from all host successes (prior + newly rendered).
        """
        start_time = time.time()
        try:
            discovered_urls, website_pages = self._discover_pages(
                base_url, max_pages, whitelist_patterns, blacklist_patterns, job_id
            )
            to_render = self._urls_to_render(discovered_urls, base_url, resume)
            self._job_repository.update_job_progress(job_id, 0, "processing", total_pages=len(discovered_urls))

            if not discovered_urls:
                self._job_repository.update_job_progress(
                    job_id, 0, "failed", "No pages found after filtering", total_pages=0
                )
                return

            # Render + convert only the pages that still need it.
            html_results = self._render_pages(to_render, job_id, len(discovered_urls))
            results = self._convert_pages(to_render, html_results, job_id, len(discovered_urls))
            self._page_error_repository.save_many(job_id, results)

            # Combined output: on resume, all host successes (regenerated); else
            # only this run's successes.
            if resume:
                success_markdowns = list(
                    self._page_error_repository.get_successful_markdown_by_base(base_url).values()
                )
            else:
                success_markdowns = [r.markdown for r in results if r.status == "success"]
            new_failures = sum(1 for r in results if r.status == "failed")

            succeeded_total = len(success_markdowns)
            if success_markdowns:
                self._save_combined_markdown(
                    job_id, base_url, ip_address, success_markdowns, website_pages.pages, start_time
                )
                failed_pages = max(0, len(discovered_urls) - succeeded_total)
                status = "completed_with_errors" if failed_pages else "completed"
                self._job_repository.update_job_progress(
                    job_id, len(discovered_urls), status, failed_pages=failed_pages
                )
            else:
                # Nothing succeeded anywhere: failed, but keep the high-water mark.
                self._job_repository.update_job_progress(
                    job_id, len(discovered_urls), "failed", failed_pages=new_failures
                )
        except Exception as error:
            logger.error("Bulk conversion job %s failed: %s", job_id, error, exc_info=True)
            self._job_repository.update_job_progress(job_id, 0, "failed", str(error))

    def _urls_to_render(
        self, discovered_urls: list[str], base_url: str, resume: bool
    ) -> list[str]:
        """Return the URLs that still need rendering (skip prior successes on resume)."""
        if not resume:
            return discovered_urls
        already = self._page_error_repository.succeeded_urls(base_url)
        return [u for u in discovered_urls if u not in already]

    def _discover_pages(
        self,
        base_url: str,
        max_pages: int,
        whitelist_patterns: list[str] | None,
        blacklist_patterns: list[str] | None,
        job_id: str,
    ) -> tuple[list[str], object]:
        """Discover and filter page URLs from the sitemap; surface truncation on the job."""
        website_pages = self._sitemap_discovery_service.discover_website_pages(base_url, max_pages=max_pages)
        page_urls = [page.loc for page in website_pages.pages]
        if whitelist_patterns:
            page_urls = [url for url in page_urls if any(p in url for p in whitelist_patterns)]
        if blacklist_patterns:
            page_urls = [url for url in page_urls if not any(p in url for p in blacklist_patterns)]
        # Surface sitemap fidelity on the job so callers can tell a capped conversion
        # from a complete one (the discovery total, before whitelist/blacklist).
        if website_pages.total_available is not None:
            self._job_repository.update_job_progress(
                job_id, 0, "processing",
                total_available=website_pages.total_available,
                truncated=website_pages.truncated,
            )
        return page_urls, website_pages

    def _render_pages(self, page_urls: list[str], job_id: str, total_pages: int) -> dict[str, str | None]:
        """Render pages and report progress."""

        def callback(completed: int) -> None:
            progress = int((completed / total_pages) * total_pages * 0.5)
            self._job_repository.update_job_progress(job_id, progress, "processing")

        return self._page_renderer.render_all(page_urls, progress_callback=callback)

    def _convert_pages(
        self,
        page_urls: list[str],
        html_results: dict[str, str | None],
        job_id: str,
        total_pages: int,
    ) -> list[PageConversionStatus]:
        """Convert rendered HTML pages to per-page conversion statuses."""
        inputs = [(url, html_results.get(url)) for url in page_urls]
        results: list[PageConversionStatus] = []

        with ThreadPoolExecutor() as executor:
            for index, status in enumerate(executor.map(self._convert_one_page, inputs)):
                results.append(status)
                progress = int(total_pages * 0.5) + (index + 1) * 0.5
                self._job_repository.update_job_progress(job_id, int(progress), "processing")
        return results

    def _convert_one_page(self, args: tuple[str, str | None]) -> PageConversionStatus:
        """Convert a single rendered page into a PageConversionStatus (never raises)."""
        url, html = args
        if not html:
            return PageConversionStatus(url=url, status="failed", error=f"No HTML content for {url}")
        try:
            markdown = self._html_to_markdown_converter.convert(html, url)
        except Exception as error:
            message = f"Error converting {url}: {error}"
            logger.error(message)
            return PageConversionStatus(url=url, status="failed", error=message)
        if not markdown or not markdown.strip():
            return PageConversionStatus(
                url=url, status="failed", error=f"Conversion resulted in empty markdown for {url}"
            )
        return PageConversionStatus(url=url, status="success", markdown=markdown)

    def _save_combined_markdown(
        self,
        job_id: str,
        base_url: str,
        ip_address: str,
        successful_markdowns: list[str],
        pages: list[SitemapUrl],
        start_time: float,
    ) -> None:
        """Combine successful markdown chunks and persist."""
        combined = "\n\n---\n\n".join(successful_markdowns)
        self._file_repository.save_markdown_file(
            MarkdownFile(
                job_id=job_id,
                content=combined,
                created_at=datetime.now(timezone.utc).isoformat(),
                ip_address=ip_address,
                file_size=len(combined.encode("utf-8")),
                generation_time_seconds=time.time() - start_time,
                base_url=base_url,
                sitemap_urls=[
                    SitemapUrl(loc=p.loc, lastmod=p.lastmod, changefreq=p.changefreq, priority=p.priority)
                    for p in pages
                ],
            )
        )
