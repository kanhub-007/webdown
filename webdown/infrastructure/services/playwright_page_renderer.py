"""
WebPageRenderer
 - Responsible for rendering web pages to HTML using Playwright.
"""

import asyncio
import logging
import sys
from collections.abc import Callable

from playwright.async_api import async_playwright

from webdown.core.domain.interfaces.page_renderer import PageRenderer
from webdown.infrastructure.services.consent_handlers.base import ConsentHandler
from webdown.infrastructure.services.consent_handlers.overlay_handler import OverlayCloseHandler
from webdown.infrastructure.services.consent_handlers.selector_handler import SelectorConsentHandler
from webdown.infrastructure.services.consent_handlers.yahoo_handler import YahooScrollConsentHandler

logger = logging.getLogger(__name__)

_AD_TRACKING_KEYWORDS = [
    "ads",
    "ad.",
    "doubleclick",
    "google-analytics",
    "tracking",
    "pixel",
    "sync",
]


_CONSENT_CHAIN: ConsentHandler | None = None


def _build_consent_chain() -> ConsentHandler:
    """Build the Chain of Responsibility for cookie consent handling."""
    yahoo = YahooScrollConsentHandler()
    selector = SelectorConsentHandler()
    overlay = OverlayCloseHandler()
    yahoo.set_next(selector).set_next(overlay)
    return yahoo


def _get_consent_chain() -> ConsentHandler:
    """Return the cached consent handler chain (built once, reused)."""
    global _CONSENT_CHAIN
    if _CONSENT_CHAIN is None:
        _CONSENT_CHAIN = _build_consent_chain()
    return _CONSENT_CHAIN


async def _handle_consent(page: object) -> bool:
    """Handle cookie consent banners using the Chain of Responsibility."""
    return await _get_consent_chain().try_handle(page)


async def _handle_consent_in_iframes(page: object, url: str) -> bool:
    """Try consent handling in content iframes (skip ad/tracking iframes)."""
    try:
        if "consent" not in url.lower() and "guce" not in url.lower():
            return False
        frames = page.frames
        checked = 0
        for frame in frames:
            if frame == page.main_frame:
                continue
            frame_url = frame.url
            if any(kw in frame_url.lower() for kw in _AD_TRACKING_KEYWORDS):
                continue
            logger.debug("PLAYWRIGHT: Trying iframe: %s", frame_url)
            if await _handle_consent(frame):
                return True
            checked += 1
            if checked >= 5:
                break
    except Exception as exc:
        logger.debug("PLAYWRIGHT: Error checking iframes: %s", exc)
    return False


async def _wait_for_redirect(page: object, original_url: str) -> str:
    """Wait for navigation after consent, return the new URL."""
    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
        await page.wait_for_timeout(2000)
    except Exception:
        pass
    return page.url


def _is_consent_page(url: str) -> bool:
    """Check if the current URL is a consent redirect page."""
    lowered = url.lower()
    return "consent" in lowered or "guce" in lowered


def _is_gitbook(url: str) -> bool:
    """Check if the URL is a GitBook documentation site."""
    return "gitbook.io" in url.lower() or ".gitbook.io" in url.lower()


async def _scroll_to_reveal(page: object) -> None:
    """Scroll the page to trigger lazy-loaded consent banners."""
    await page.evaluate("() => window.scrollTo(0, window.innerHeight)")
    await page.wait_for_timeout(500)
    await page.mouse.move(100, 100)
    await page.wait_for_timeout(500)
    await page.evaluate("() => window.scrollTo(0, 0)")
    await page.wait_for_timeout(500)


async def _scroll_to_bottom(page: object) -> None:
    """Scroll to the bottom of the page to load lazy content."""
    await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(3000)


async def _process_consent_page(page: object, url: str) -> str:
    """Handle a consent redirect page with retries and iframe support."""
    logger.info("PLAYWRIGHT: Detected consent redirect page: %s", url)
    await page.wait_for_timeout(3000)

    try:
        await page.wait_for_selector("[class*='gdpr'], [class*='consent'], [class*='fineprint'], form", timeout=5000)
        logger.info("PLAYWRIGHT: Consent form loaded")
    except Exception:
        logger.debug("PLAYWRIGHT: No consent form selector matched")

    for i in range(3):
        await page.evaluate(f"() => window.scrollTo(0, {(i + 1) * 500})")
        await page.wait_for_timeout(300)
    await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(1000)

    for attempt in range(5):
        current = page.url
        if not _is_consent_page(current):
            logger.info("PLAYWRIGHT: No longer on consent page")
            break

        logger.debug("PLAYWRIGHT: Consent attempt %d/5", attempt + 1)
        handled = await _handle_consent(page)
        if not handled:
            handled = await _handle_consent_in_iframes(page, current)

        if handled:
            new_url = await _wait_for_redirect(page, url)
            logger.info("PLAYWRIGHT: Redirected to: %s", new_url)
            if not _is_consent_page(new_url):
                break
            await page.wait_for_timeout(1000)
        else:
            await page.wait_for_timeout(1000)

    try:
        await page.wait_for_load_state("load", timeout=15000)
    except Exception:
        pass
    await page.wait_for_timeout(2000)
    return page.url


async def _process_regular_page(page: object) -> None:
    """Handle inline consent modals on a non-redirect page."""
    await page.wait_for_timeout(2000)
    try:
        await page.wait_for_selector("[class*='gdpr'], [class*='consent'], [class*='fineprint']", timeout=3000)
        logger.info("PLAYWRIGHT: Detected consent modal")
    except Exception:
        logger.debug("PLAYWRIGHT: No specific consent modal found")

    await _scroll_to_reveal(page)

    for _attempt in range(3):
        handled = await _handle_consent(page)
        if handled:
            await page.wait_for_timeout(1500)
            await _handle_consent(page)
        else:
            break


async def _process_page(page: object, url: str) -> str:
    """Process a page: navigate, handle consent, scroll, extract HTML.

    Uses Template Method pattern — each step is a separate function.
    """
    logger.info("PLAYWRIGHT: Navigating to %s", url)
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_load_state("load")

    if _is_gitbook(url):
        logger.info("PLAYWRIGHT: GitBook URL detected — skipping consent checks")
        try:
            await page.wait_for_selector("body", timeout=20000)
        except Exception:
            pass
        await _scroll_to_bottom(page)
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
            logger.debug("PLAYWRIGHT: Network idle after scroll (GitBook)")
        except Exception:
            logger.debug("PLAYWRIGHT: Network idle timeout — continuing anyway (GitBook)")
        html = await page.content()
        logger.debug("PLAYWRIGHT: Got HTML (%d chars)", len(html))
        return html

    if _is_consent_page(page.url):
        await _process_consent_page(page, url)
    else:
        await _process_regular_page(page)

    try:
        await page.wait_for_selector("body", timeout=20000)
    except Exception:
        pass
    await _scroll_to_bottom(page)
    await _handle_consent(page)

    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
        logger.debug("PLAYWRIGHT: Network idle after scroll")
    except Exception:
        logger.debug("PLAYWRIGHT: Network idle timeout — continuing anyway")

    html = await page.content()
    logger.debug("PLAYWRIGHT: Got HTML (%d chars)", len(html))
    return html


async def _render(url: str) -> str:
    logger.info("PLAYWRIGHT: Launching browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1024, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        page = await context.new_page()
        html = await _process_page(page, url)
        logger.debug("PLAYWRIGHT: First 1000 chars:\n%s", html[:1000])
        await browser.close()
        return html


async def _render_all(urls: list[str], max_concurrent: int = 5, progress_callback=None) -> dict[str, str]:
    logger.info(
        "PLAYWRIGHT: Launching browser for %d URLs with %d concurrent tabs...",
        len(urls),
        max_concurrent,
    )
    results: dict[str, str] = {}
    semaphore = asyncio.Semaphore(max_concurrent)
    completed_count = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )

        async def process_url(url: str) -> tuple[str, str]:
            nonlocal completed_count
            page = None
            async with semaphore:
                logger.info("PLAYWRIGHT: Processing %s", url)
                try:
                    page = await context.new_page()
                    html = await _process_page(page, url)
                    await page.close()
                    completed_count += 1
                    if progress_callback:
                        progress_callback(completed_count)
                    return url, html
                except asyncio.CancelledError:
                    logger.warning("PLAYWRIGHT: Processing cancelled for %s", url)
                    if page and not page.is_closed():
                        try:
                            await page.close()
                        except Exception:
                            pass
                    completed_count += 1
                    if progress_callback:
                        progress_callback(completed_count)
                    return url, ""
                except Exception as exc:
                    logger.error("PLAYWRIGHT: Failed to process %s: %s", url, exc)
                    if page and not page.is_closed():
                        try:
                            await page.close()
                        except Exception:
                            pass
                    completed_count += 1
                    if progress_callback:
                        progress_callback(completed_count)
                    return url, ""

        tasks = [process_url(url) for url in urls]
        try:
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            for item in completed:
                if isinstance(item, tuple) and len(item) == 2:
                    url, html = item
                    results[url] = html
                elif isinstance(item, Exception):
                    logger.error("PLAYWRIGHT: Task failed: %s", item)
        except asyncio.CancelledError:
            logger.warning("PLAYWRIGHT: Batch cancelled, cleaning up...")
            for task in tasks:
                if not task.done():
                    task.cancel()
            raise

        await browser.close()
    return results


def render(url: str) -> str:
    """Synchronous wrapper for rendering a single URL."""
    return asyncio.run(_render(url))


def render_all(urls: list[str], max_concurrent: int = 5, progress_callback=None) -> dict[str, str]:
    """Synchronous wrapper for rendering multiple URLs concurrently."""
    return asyncio.run(_render_all(urls, max_concurrent, progress_callback))


class PlaywrightPageRenderer(PageRenderer):
    """Page renderer backed by Playwright."""

    def __init__(self, max_concurrent: int = 5) -> None:
        """Initialize with a concurrency limit.

        Sets the Windows Proactor event loop policy if needed — this is the
        correct place because the policy must be in place before any asyncio
        event loop is created, and the renderer is the first consumer.
        """
        if sys.platform == "win32" and sys.version_info < (3, 14):
            try:
                # Proactor event loop policy is required for asyncio subprocess
                # support on Windows before Python 3.14 (where it became default).
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except Exception:
                pass  # Already set or incompatible platform
        self._max_concurrent = max_concurrent

    def render(self, url: str) -> str | None:
        """Render one URL to HTML."""
        return render(url)

    def render_all(
        self,
        urls: list[str],
        progress_callback: Callable[[int], None] | None = None,
    ) -> dict[str, str | None]:
        """Render multiple URLs to HTML."""
        return render_all(urls, self._max_concurrent, progress_callback)
