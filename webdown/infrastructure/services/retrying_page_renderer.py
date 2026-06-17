"""RetryingPageRenderer — a Decorator around PageRenderer for transient-rate-limit retry.

Detects render outputs that look transient (tiny body with no content landmark)
and retries with exponential backoff. After ``max_attempts`` the last result is
returned unchanged, so downstream resilience still records honest failures.

Implements both ``render`` and ``render_all`` (transparent to callers). Wired
default-on in ``service_factory`` so single-page AND bulk paths are protected.
See specs/2026-06-16_render-retry-backoff/.
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable

from webdown.core.domain.entities.retry_config import RetryConfig
from webdown.core.domain.interfaces.page_renderer import PageRenderer

logger = logging.getLogger(__name__)


def _looks_transient(html: str | None, *, config: RetryConfig) -> bool:
    """Return True when the rendered body looks like a transient error/rate-limit.

    ``None``/empty is transient.  A body >= ``min_valid_chars`` is real
    (short-circuit — most pages are large).  A small body with a landmark
    (``<article>``, ``<main>``, etc.) is real; a small body without one is
    likely a 429 / consent / error page.
    """
    if html is None:
        return True
    stripped = html.strip()
    if not stripped:
        return True
    if len(stripped) >= config.min_valid_chars:
        return False
    lowered = stripped.lower()
    return not any(lm in lowered for lm in config.landmarks)


class RetryingPageRenderer(PageRenderer):
    """Wraps a PageRenderer and retries transient outputs with backoff."""

    def __init__(
        self,
        inner: PageRenderer,
        config: RetryConfig = RetryConfig(),
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._inner = inner
        self._config = config
        self._sleep = sleep

    @property
    def inner(self) -> PageRenderer:
        """The wrapped renderer (used by factory-wiring tests)."""
        return self._inner

    # ---- render (single URL) ----

    def render(self, url: str) -> str | None:
        """Render a URL, retrying up to max_attempts on transient results."""
        attempt = 0
        last: str | None = None
        while attempt < self._config.max_attempts:
            attempt += 1
            try:
                last = self._inner.render(url)
            except Exception:
                # Exceptions are NOT retried — re-raise immediately so
                # cancellation (CancelledError) propagates cleanly.
                raise
            if not _looks_transient(last, config=self._config):
                return last
            if attempt < self._config.max_attempts:
                self._backoff_and_log(attempt, url)
        # Cap reached: return the last transient body unchanged (no fabrication).
        return last

    # ---- render_all (bulk batch) ----

    def render_all(
        self,
        urls: list[str],
        progress_callback: Callable[[int], None] | None = None,
    ) -> dict[str, str | None]:
        """Render a batch; transient URLs are retried in one batched call per wave.

        ``progress_callback`` is forwarded to the inner renderer for the first
        pass only.  During retry waves it is set to ``None`` to prevent the
        callback from counting from zero and overwriting the first-pass
        high-water mark (the bulk use case computes ``completed * 0.5``, so
        a retry counter reset would regress job progress).
        """
        results = self._inner.render_all(urls, progress_callback=progress_callback)
        transient = [u for u in urls if _looks_transient(results.get(u), config=self._config)]

        attempt = 1  # the first pass above was attempt 1
        while transient and attempt < self._config.max_attempts:
            self._backoff_and_log(attempt, list(transient)[:5])
            attempt += 1
            # Second and subsequent passes: no callback (see docstring).
            retry_results = self._inner.render_all(transient, progress_callback=None)
            results.update(retry_results)
            transient = [u for u in transient if _looks_transient(retry_results.get(u), config=self._config)]

        return results

    # ---- helpers ----

    def _backoff_and_log(self, attempt_index: int, context: object) -> None:
        """Sleep for a backoff delay and log the retry."""
        delay = self._config.base_delay_seconds * (2 ** (attempt_index - 1))
        if self._config.jitter:
            delay = random.uniform(0, delay)
        logger.warning(
            "Retrying render (attempt %d/%d, %.2fs) for %s",
            attempt_index + 1,
            self._config.max_attempts,
            delay,
            context,
        )
        self._sleep(delay)
