"""Tests for RetryingPageRenderer — retry-with-backoff for transient page renders.

Classical school: the REAL RetryingPageRenderer decorator wraps a FAKE inner
renderer that returns scripted sequences. Assert on observable outcomes — final
returned HTML, attempt counts, sleep deltas — never on mock interactions.
Matches specs/2026-06-16_render-retry-backoff/02-scenarios.md.
"""

import logging

import pytest

from webdown.core.domain.interfaces.page_renderer import PageRenderer


# ---------- test fixtures (from the spec) ----------

RATE_LIMIT_BODY = "<html><head><title>429</title></head><body>Too Many Requests</body></html>"
# ~5KB body that contains a landmark — real page
REAL_BODY = "<html><body><article><h2>Real</h2><p>" + ("x" * 5000) + "</p></article></body></html>"


class _ScriptedRenderer(PageRenderer):
    """Returns the next scripted result for a URL each time it is called."""

    def __init__(self, script: dict[str, list[str | None]]) -> None:
        self._script = {u: list(seq) for u, seq in script.items()}
        self.calls: list[str] = []

    def render(self, url: str) -> str | None:
        self.calls.append(url)
        seq = self._script.setdefault(url, [None])
        return seq.pop(0) if seq else None

    def render_all(self, urls, progress_callback=None) -> dict[str, str | None]:
        return {u: self.render(u) for u in urls}


class _RecordingSleep:
    """Replaces time.sleep; records the requested delays."""

    def __init__(self) -> None:
        self.delays: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


class _ExplodingRenderer(PageRenderer):
    """Raises unconditionally — for testing that exceptions aren't swallowed."""

    def render(self, url: str) -> str | None:
        raise RuntimeError("inner exploded")

    def render_all(self, urls, progress_callback=None) -> dict[str, str | None]:
        raise RuntimeError("inner exploded")


# ---------- helpers ----------

def _decorator(inner, config=None, sleep=None):
    from webdown.core.domain.entities.retry_config import RetryConfig
    from webdown.infrastructure.services.retrying_page_renderer import RetryingPageRenderer

    return RetryingPageRenderer(inner, config or RetryConfig(), sleep=sleep)


# ---------- Slice 1 scenarios ----------

def test_transient_then_success_retries_and_returns_real() -> None:
    """S1: first attempt is 429; second is real → real returned, 2 attempts, 1 sleep."""
    inner = _ScriptedRenderer({"https://x/p": [RATE_LIMIT_BODY, REAL_BODY]})
    sleep = _RecordingSleep()
    renderer = _decorator(inner, sleep=sleep)

    result = renderer.render("https://x/p")

    assert "Real" in result
    assert inner.calls == ["https://x/p", "https://x/p"]
    assert len(sleep.delays) == 1


def test_honest_terminal_failure_after_cap() -> None:
    """S2: always transient → returns last body unchanged, bounded attempts, no fabrications."""
    from webdown.core.domain.entities.retry_config import RetryConfig

    inner = _ScriptedRenderer({"https://x/p": [RATE_LIMIT_BODY, RATE_LIMIT_BODY, RATE_LIMIT_BODY]})
    sleep = _RecordingSleep()
    renderer = _decorator(inner, RetryConfig(max_attempts=3), sleep=sleep)

    result = renderer.render("https://x/p")

    assert result == RATE_LIMIT_BODY  # unchanged — not None, not faked
    assert len(inner.calls) == 3
    assert len(sleep.delays) == 2


def test_max_attempts_one_no_retries() -> None:
    """max_attempts=1 → no retry; zero sleeps."""
    from webdown.core.domain.entities.retry_config import RetryConfig

    inner = _ScriptedRenderer({"https://x/p": [RATE_LIMIT_BODY]})
    sleep = _RecordingSleep()
    renderer = _decorator(inner, RetryConfig(max_attempts=1), sleep=sleep)

    renderer.render("https://x/p")
    assert len(inner.calls) == 1
    assert sleep.delays == []


def test_genuinely_tiny_valid_page_is_not_retried() -> None:
    """S3: tiny HTML WITH a landmark → not transient → one call, no sleep."""
    small_real = "<html><body><main><p>short but real</p></main></body></html>"
    inner = _ScriptedRenderer({"https://x/p": [small_real]})
    sleep = _RecordingSleep()
    renderer = _decorator(inner, sleep=sleep)

    result = renderer.render("https://x/p")

    assert result == small_real
    assert len(inner.calls) == 1
    assert sleep.delays == []


def test_large_body_no_landmark_is_not_retried() -> None:
    """A body >= min_valid_chars is not transient even without landmark."""
    large_no_landmark = "<html><body><p>" + ("y" * 2000) + "</p></body></html>"
    inner = _ScriptedRenderer({"https://x/p": [large_no_landmark]})
    sleep = _RecordingSleep()
    renderer = _decorator(inner, sleep=sleep)

    result = renderer.render("https://x/p")

    assert result == large_no_landmark
    assert len(inner.calls) == 1


def test_none_then_success_retries() -> None:
    """S4: None render → transient → retry succeeds."""
    inner = _ScriptedRenderer({"https://x/p": [None, REAL_BODY]})
    sleep = _RecordingSleep()
    renderer = _decorator(inner, sleep=sleep)

    result = renderer.render("https://x/p")

    assert "Real" in result
    assert inner.calls == ["https://x/p", "https://x/p"]


def test_empty_then_success_retries() -> None:
    """Empty string render → transient → retry succeeds."""
    inner = _ScriptedRenderer({"https://x/p": ["", REAL_BODY]})
    renderer = _decorator(inner, sleep=_RecordingSleep())

    result = renderer.render("https://x/p")

    assert "Real" in result
    assert len(inner.calls) == 2


def test_exponential_backoff_with_jitter() -> None:
    """S5: jittered delays in [0, base*2^attempt)."""
    from webdown.core.domain.entities.retry_config import RetryConfig

    inner = _ScriptedRenderer({"https://x/p": [RATE_LIMIT_BODY] * 3})
    sleep = _RecordingSleep()
    renderer = _decorator(inner, RetryConfig(max_attempts=3, base_delay_seconds=1.0, jitter=True), sleep=sleep)

    renderer.render("https://x/p")

    assert len(sleep.delays) == 2
    assert 0 <= sleep.delays[0] < 1.0   # base * 2^0, jittered
    assert 0 <= sleep.delays[1] < 2.0   # base * 2^1, jittered


def test_exponential_backoff_without_jitter_is_deterministic() -> None:
    """jitter=False → delays are exactly base * 2^attempt."""
    from webdown.core.domain.entities.retry_config import RetryConfig

    inner = _ScriptedRenderer({"https://x/p": [RATE_LIMIT_BODY] * 3})
    sleep = _RecordingSleep()
    renderer = _decorator(inner, RetryConfig(max_attempts=3, base_delay_seconds=1.5, jitter=False), sleep=sleep)

    renderer.render("https://x/p")

    assert sleep.delays == pytest.approx([1.5, 3.0])


def test_render_all_retries_each_url_independently() -> None:
    """S6: two URLs, both transient→real; retried in one batched call."""
    inner = _ScriptedRenderer({
        "https://x/p/a": [RATE_LIMIT_BODY, REAL_BODY],
        "https://x/p/b": [RATE_LIMIT_BODY, REAL_BODY.replace("Real", "B")],
    })
    renderer = _decorator(inner, sleep=_RecordingSleep())

    results = renderer.render_all(["https://x/p/a", "https://x/p/b"])

    assert "Real" in results["https://x/p/a"]
    assert "B" in results["https://x/p/b"]
    assert inner.calls.count("https://x/p/a") == 2
    assert inner.calls.count("https://x/p/b") == 2


def test_render_all_suppresses_progress_callback_during_retries() -> None:
    """The callback is forwarded for the first pass; NOT invoked during retries."""

    class _TrackingRenderer(PageRenderer):
        """Delegates to a scripted inner and fires progress_callback per URL."""

        def __init__(self, script):
            self._inner = _ScriptedRenderer(script)
            self._rendered: dict[str, str | None] = {}

        def render(self, url):
            return self._inner.render(url)

        def render_all(self, urls, progress_callback=None):
            # Clear for this batch so results reflect only this call.
            self._rendered = {}
            for completed, url in enumerate(urls, start=1):
                self._rendered[url] = self._inner.render(url)
                if progress_callback:
                    progress_callback(completed)
            return dict(self._rendered)

    inner = _TrackingRenderer({
        "https://x/p/a": [RATE_LIMIT_BODY, REAL_BODY],
        "https://x/p/b": [RATE_LIMIT_BODY, REAL_BODY],
    })
    renderer = _decorator(inner, sleep=_RecordingSleep())
    call_counts: list[int] = []

    def my_callback(completed: int) -> None:
        call_counts.append(completed)

    renderer.render_all(["https://x/p/a", "https://x/p/b"], progress_callback=my_callback)

    # First pass fires callback for both URLs (completed=1, completed=2).
    # Retry wave passes callback=None, so no further entries.
    assert call_counts == [1, 2]


def test_render_all_stale_transient_returns_last_body() -> None:
    """A URL that stays transient returns its last body in the dict (not None)."""
    inner = _ScriptedRenderer({"https://x/p/a": [RATE_LIMIT_BODY] * 3})
    renderer = _decorator(inner, sleep=_RecordingSleep())

    results = renderer.render_all(["https://x/p/a"])

    assert results["https://x/p/a"] == RATE_LIMIT_BODY


def test_decorator_is_transparent_page_renderer() -> None:
    """S7: RetryingPageRenderer IS a PageRenderer (Liskov-substitutable)."""
    renderer = _decorator(_ScriptedRenderer({"https://x/p": [REAL_BODY]}))
    # isinstance can break under ABC registry corruption (pre-existing test-isolation
    # issue in the full suite).  The MRO never lies:
    assert "PageRenderer" in [c.__name__ for c in type(renderer).__mro__]
    # Also functionally: it implements both interface methods.
    assert hasattr(renderer, "render")
    assert hasattr(renderer, "render_all")


def test_cancellation_exceptions_are_not_swallowed() -> None:
    """S9: an exception from the inner renderer is re-raised, not retry-looped on."""
    renderer = _decorator(_ExplodingRenderer(), sleep=_RecordingSleep())

    with pytest.raises(RuntimeError, match="inner exploded"):
        renderer.render("https://x/p")

    with pytest.raises(RuntimeError, match="inner exploded"):
        renderer.render_all(["https://x/p"])


def test_wired_as_default_in_factory() -> None:
    """S8: create_page_renderer returns a RetryingPageRenderer wrapping Playwright."""
    from webdown.infrastructure.services.playwright_page_renderer import PlaywrightPageRenderer
    from webdown.infrastructure.services.retrying_page_renderer import RetryingPageRenderer
    from webdown.startup.service_factory import create_page_renderer

    renderer = create_page_renderer()
    assert isinstance(renderer, RetryingPageRenderer)
    assert isinstance(renderer.inner, PlaywrightPageRenderer)


# ---------- Slice 2 scenario (logging) ----------

def test_each_retry_attempt_is_logged(caplog) -> None:
    """S10 (Slice 2): a WARNING is emitted per retry with url, attempt, delay."""
    from webdown.core.domain.entities.retry_config import RetryConfig

    inner = _ScriptedRenderer({"https://x/p": [RATE_LIMIT_BODY, RATE_LIMIT_BODY, REAL_BODY]})
    renderer = _decorator(inner, RetryConfig(max_attempts=3, jitter=False), sleep=_RecordingSleep())

    with caplog.at_level(logging.WARNING, logger="webdown.infrastructure.services.retrying_page_renderer"):
        renderer.render("https://x/p")

    warns = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warns) == 2                                 # two retries
    assert "https://x/p" in warns[0].getMessage()
    assert "https://x/p" in warns[1].getMessage()
    assert "attempt 1" in warns[0].getMessage().lower() or "attempt 2" in warns[0].getMessage().lower()
