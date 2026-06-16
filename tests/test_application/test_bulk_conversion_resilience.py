"""Tests for GenerateAllPagesMarkdownUseCase resilience behaviour.

Classical school: REAL converter (no I/O), in-memory fakes at the persistence
and rendering boundaries. Asserts on observable outcomes, never on interactions.

Covers spec scenarios S1, S3, S4, S5 from
specs/2026-06-16_bulk-conversion-resilience/02-scenarios.md
"""

from webdown.core.application.use_cases.generate_all_pages_markdown import (
    GenerateAllPagesMarkdownUseCase,
)
from webdown.core.domain.entities.sitemap_url import SitemapUrl
from webdown.core.domain.entities.website_pages import WebsitePages
from webdown.infrastructure.services.beautifulsoup_html_to_markdown_converter import (
    BeautifulSoupHtmlToMarkdownConverter,
)
from tests.test_application._fakes import (
    InMemoryMarkdownFileRepository,
    InMemoryMarkdownJobRepository,
    InMemoryPageErrorRepository,
)

BASE = "https://x.com"
GOOD_HTML = "<html><body><article><h2>{title}</h2><p>{body}</p></article></body></html>"
# Heading-only page -> the real converter returns "" (no content beyond headings).
EMPTY_HTML = "<html><body><article><h2>Only A Heading</h2></article></body></html>"


class _FakeRenderer:
    """Returns canned HTML per URL; URLs absent from the map render to None."""

    def __init__(self, html_by_url: dict[str, str | None]) -> None:
        self._html = html_by_url
        self.rendered: list[str] = []

    def render_all(self, urls, progress_callback=None) -> dict[str, str | None]:
        out = {}
        for u in urls:
            self.rendered.append(u)
            out[u] = self._html.get(u)
        return out


class _FakeDiscovery:
    """Returns a fixed list of discovered pages."""

    def __init__(self, pages: list[SitemapUrl]) -> None:
        self._pages = pages

    def discover_website_pages(self, base_url, max_pages=None) -> WebsitePages:
        return WebsitePages(pages=list(self._pages))


def _build_use_case(html_by_url, pages, converter=None, page_error_repo=None):
    """Wire the use case with real converter + in-memory fakes."""
    job_repo = InMemoryMarkdownJobRepository()
    file_repo = InMemoryMarkdownFileRepository()
    error_repo = page_error_repo or InMemoryPageErrorRepository()
    use_case = GenerateAllPagesMarkdownUseCase(
        job_repository=job_repo,
        file_repository=file_repo,
        sitemap_discovery_service=_FakeDiscovery(pages),
        page_renderer=_FakeRenderer(html_by_url),
        html_to_markdown_converter=converter or BeautifulSoupHtmlToMarkdownConverter(),
        page_error_repository=error_repo,
    )
    return use_case, job_repo, file_repo, error_repo


def _run(use_case, job_repo, job_id, base_url):
    """Mirror production: create the job, then execute (StartAllPages... does this)."""
    job_repo.create_job(job_id, 0)
    use_case.execute(job_id, base_url, 10, None, None, "mcp")


def test_partial_failure_marks_completed_with_errors_and_saves_successes() -> None:
    """S1: page B fails; A and C are still saved; status is completed_with_errors."""
    pages = [
        SitemapUrl(loc=f"{BASE}/p/a"),
        SitemapUrl(loc=f"{BASE}/p/b"),
        SitemapUrl(loc=f"{BASE}/p/c"),
    ]
    html = {
        f"{BASE}/p/a": GOOD_HTML.format(title="A", body="Body of A."),
        f"{BASE}/p/b": None,  # renders to None -> "No HTML content" failure
        f"{BASE}/p/c": GOOD_HTML.format(title="C", body="Body of C."),
    }
    use_case, job_repo, file_repo, error_repo = _build_use_case(html, pages)
    _run(use_case, job_repo, "J", BASE)

    progress = job_repo.get_job_progress("J")
    assert progress.status == "completed_with_errors"
    assert progress.processed_pages == 3  # high-water mark
    assert progress.failed_pages == 1

    saved = file_repo.get_markdown_file("J")
    assert saved is not None
    assert "Body of A" in saved.content
    assert "Body of C" in saved.content

    errors = error_repo.get_by_job("J")
    failed = [e.url for e in errors if e.status == "failed"]
    assert failed == [f"{BASE}/p/b"]


def test_all_success_marks_completed_with_zero_failures() -> None:
    """Full success keeps status 'completed' and failed_pages == 0."""
    pages = [SitemapUrl(loc=f"{BASE}/p/a"), SitemapUrl(loc=f"{BASE}/p/c")]
    html = {f"{BASE}/p/a": GOOD_HTML.format(title="A", body="A body."),
            f"{BASE}/p/c": GOOD_HTML.format(title="C", body="C body.")}
    use_case, job_repo, file_repo, _ = _build_use_case(html, pages)
    _run(use_case, job_repo, "J", BASE)

    progress = job_repo.get_job_progress("J")
    assert progress.status == "completed"
    assert progress.failed_pages == 0
    assert file_repo.get_markdown_file("J") is not None


def test_all_fail_marks_failed_and_saves_no_file_but_keeps_manifest() -> None:
    """S5: every page fails -> status 'failed', no MarkdownFile, manifest complete."""
    pages = [SitemapUrl(loc=f"{BASE}/p/b"), SitemapUrl(loc=f"{BASE}/p/d")]
    html = {f"{BASE}/p/b": None, f"{BASE}/p/d": EMPTY_HTML}
    use_case, job_repo, file_repo, error_repo = _build_use_case(html, pages)
    _run(use_case, job_repo, "J", BASE)

    progress = job_repo.get_job_progress("J")
    assert progress.status == "failed"
    assert progress.failed_pages == 2
    assert progress.processed_pages == 2  # high-water mark, NOT reset to 0
    assert file_repo.get_markdown_file("J") is None
    assert len(error_repo.get_by_job("J")) == 2  # manifest still complete


def test_converter_exception_is_isolated_not_job_fatal() -> None:
    """A converter exception on one page is recorded; other pages still succeed.

    The converter bug that originally crashed was fixed, so we inject a tiny
    subclass that raises for one URL to exercise the exception-handling branch
    directly. This is a controlled failure for the try/except path, not a mock
    of domain logic.
    """

    class _RaisingConverter(BeautifulSoupHtmlToMarkdownConverter):
        def convert(self, html, base_url):
            if base_url.endswith("/p/b"):
                raise RuntimeError("boom from converter")
            return super().convert(html, base_url)

    pages = [SitemapUrl(loc=f"{BASE}/p/a"), SitemapUrl(loc=f"{BASE}/p/b")]
    use_case, job_repo, file_repo, error_repo = _build_use_case(
        pages=pages,
        html_by_url={
            f"{BASE}/p/a": GOOD_HTML.format(title="A", body="Body of A."),
            f"{BASE}/p/b": GOOD_HTML.format(title="B", body="Body of B."),
        },
        converter=_RaisingConverter(),
    )
    _run(use_case, job_repo, "J", BASE)

    progress = job_repo.get_job_progress("J")
    assert progress.status == "completed_with_errors"
    assert progress.failed_pages == 1
    saved = file_repo.get_markdown_file("J")
    assert saved is not None and "Body of A" in saved.content
    failed = [e for e in error_repo.get_by_job("J") if e.status == "failed"]
    assert len(failed) == 1
    assert failed[0].url == f"{BASE}/p/b"
    assert "boom from converter" in (failed[0].error or "")


def test_per_page_markdown_is_stored_for_successful_pages() -> None:
    """C2: successful pages' markdown is stored so split_per_page export can read it."""
    pages = [SitemapUrl(loc=f"{BASE}/p/a"), SitemapUrl(loc=f"{BASE}/p/b")]
    html = {
        f"{BASE}/p/a": GOOD_HTML.format(title="A", body="Body of A."),
        f"{BASE}/p/b": None,  # failure
    }
    use_case, job_repo, _, error_repo = _build_use_case(html, pages)
    _run(use_case, job_repo, "J", BASE)

    success_md = error_repo.get_successful_markdown("J")
    assert set(success_md.keys()) == {f"{BASE}/p/a"}
    assert "Body of A" in success_md[f"{BASE}/p/a"]


def test_resume_skips_succeeded_urls_and_regenerates_combined_output() -> None:
    """S6 + M3: resume renders only gaps; combined output includes prior successes."""
    from webdown.core.domain.entities.page_conversion_status import PageConversionStatus

    # A prior run already succeeded on A and C (stored under an old job id).
    prior_repo = InMemoryPageErrorRepository()
    prior_repo.save_many("OLD", [
        PageConversionStatus(url=f"{BASE}/p/a", status="success", markdown="# A\n\nprior A body"),
        PageConversionStatus(url=f"{BASE}/p/c", status="success", markdown="# C\n\nprior C body"),
    ])
    discovered = [SitemapUrl(loc=f"{BASE}/p/a"), SitemapUrl(loc=f"{BASE}/p/b"), SitemapUrl(loc=f"{BASE}/p/c")]
    renderer = _FakeRenderer({f"{BASE}/p/b": GOOD_HTML.format(title="B", body="new B body")})
    job_repo = InMemoryMarkdownJobRepository()
    file_repo = InMemoryMarkdownFileRepository()
    use_case = GenerateAllPagesMarkdownUseCase(
        job_repo, file_repo, _FakeDiscovery(discovered), renderer,
        BeautifulSoupHtmlToMarkdownConverter(), prior_repo,
    )

    job_repo.create_job("J2", 0)
    use_case.execute("J2", BASE, 10, None, None, "mcp", resume=True)

    # Only the gap (B) was rendered — A and C were skipped.
    assert set(renderer.rendered) == {f"{BASE}/p/b"}
    # Combined output is regenerated from ALL host successes (prior + new).
    saved = file_repo.get_markdown_file("J2")
    assert saved is not None
    assert "prior A body" in saved.content
    assert "prior C body" in saved.content
    assert "new B body" in saved.content
    progress = job_repo.get_job_progress("J2")
    assert progress.status == "completed"  # all 3 discovered now succeeded
    assert progress.failed_pages == 0


class _RecordingCrashWriter:
    """In-memory crash artifact writer that records what it was asked to save."""

    def __init__(self) -> None:
        self.saved: dict[str, tuple[str, str, str]] = {}  # url -> (path, html, traceback)

    def write(self, job_id: str, url: str, html: str, traceback_text: str) -> str:
        path = f"debug/{job_id}/{url.rsplit('/', 1)[-1]}.html"
        self.saved[url] = (path, html, traceback_text)
        return path


def test_crash_artifacts_captured_on_converter_exception() -> None:
    """Slice 3: when capture_artifacts=True, a converter crash saves HTML + traceback."""

    class _RaisingConverter(BeautifulSoupHtmlToMarkdownConverter):
        def convert(self, html, base_url):
            if base_url.endswith("/p/b"):
                raise RuntimeError("boom")
            return super().convert(html, base_url)

    pages = [SitemapUrl(loc=f"{BASE}/p/a"), SitemapUrl(loc=f"{BASE}/p/b")]
    crash_writer = _RecordingCrashWriter()
    error_repo = InMemoryPageErrorRepository()
    job_repo = InMemoryMarkdownJobRepository()
    use_case = GenerateAllPagesMarkdownUseCase(
        job_repo, InMemoryMarkdownFileRepository(), _FakeDiscovery(pages),
        _FakeRenderer({
            f"{BASE}/p/a": GOOD_HTML.format(title="A", body="Body of A."),
            f"{BASE}/p/b": "<html>offending html for b</html>",
        }),
        _RaisingConverter(), error_repo, crash_artifact_writer=crash_writer,
    )

    job_repo.create_job("J", 0)
    use_case.execute("J", BASE, 10, None, None, "mcp", capture_artifacts=True)

    # The failing page's artifact was captured and referenced from its status.
    assert f"{BASE}/p/b" in crash_writer.saved
    path, html, tb = crash_writer.saved[f"{BASE}/p/b"]
    assert "offending html for b" in html
    assert "RuntimeError" in tb and "boom" in tb
    assert path.endswith("b.html")
    failed = [s for s in error_repo.get_by_job("J") if s.status == "failed"]
    assert failed[0].artifact_path == path


def test_crash_artifacts_not_captured_by_default() -> None:
    """capture_artifacts defaults off — no files written, status still records the error."""

    class _RaisingConverter(BeautifulSoupHtmlToMarkdownConverter):
        def convert(self, html, base_url):
            raise RuntimeError("always boom")

    pages = [SitemapUrl(loc=f"{BASE}/p/b")]
    crash_writer = _RecordingCrashWriter()
    job_repo = InMemoryMarkdownJobRepository()
    use_case = GenerateAllPagesMarkdownUseCase(
        job_repo, InMemoryMarkdownFileRepository(), _FakeDiscovery(pages),
        _FakeRenderer({f"{BASE}/p/b": "<html>x</html>"}),
        _RaisingConverter(), InMemoryPageErrorRepository(), crash_artifact_writer=crash_writer,
    )

    job_repo.create_job("J", 0)
    use_case.execute("J", BASE, 10, None, None, "mcp")  # capture_artifacts defaults False

    assert crash_writer.saved == {}  # nothing captured
