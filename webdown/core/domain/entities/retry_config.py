"""Domain entity for retry configuration — a frozen value object.

Configures the RetryingPageRenderer decorator: how many retries, what backoff
schedule, and the content-heuristic thresholds for detecting transient responses.
See specs/2026-06-16_render-retry-backoff/03-domain.md.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RetryConfig:
    """Behaviour knobs for retrying transient page renders.

    All fields have sensible defaults; construct with keyword overrides only.
    """

    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    jitter: bool = True
    min_valid_chars: int = 1500
    landmarks: tuple[str, ...] = ("<article", "<main")
