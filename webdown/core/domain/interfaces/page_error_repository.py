"""Domain repository interface for per-page conversion status (resilience).

Persists each page's outcome during a bulk conversion so that:
  - a few failing pages never discard the successes (error isolation);
  - the full failure manifest is queryable (no truncation);
  - successful pages' markdown can be re-read for per-page export / resume.
"""

from abc import ABC, abstractmethod

from webdown.core.domain.entities.page_conversion_status import PageConversionStatus


class PageErrorRepository(ABC):
    """Stores per-page conversion outcomes for a bulk markdown job."""

    @abstractmethod
    def save(self, job_id: str, status: PageConversionStatus) -> None:
        """Persist one page's conversion outcome (upsert on (job_id, url))."""

    @abstractmethod
    def save_many(self, job_id: str, statuses: list[PageConversionStatus]) -> None:
        """Persist many page outcomes (upsert on (job_id, url))."""

    @abstractmethod
    def get_by_job(self, job_id: str) -> list[PageConversionStatus]:
        """Return all recorded page outcomes for a job (successes and failures)."""

    @abstractmethod
    def get_successful_markdown(self, job_id: str) -> dict[str, str]:
        """Return {url: markdown} for the successful pages of a job.

        Enables per-page export (split_per_page) without re-converting.
        """

    @abstractmethod
    def get_successful_markdown_by_base(self, base_url: str) -> dict[str, str]:
        """Return {url: markdown} for all successful pages under a base_url (cross-job).

        Enables resume: the regenerated combined output includes prior successes
        stored under previous job ids for the same site.
        """

    @abstractmethod
    def succeeded_urls(self, base_url: str) -> set[str]:
        """Return URLs already converted successfully for a base_url.

        Enables resume: re-running a job skips these pages.
        """
