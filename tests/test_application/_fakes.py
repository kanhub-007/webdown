"""Shared in-memory test fakes for the persistence boundary.

Classical school: these give REAL behaviour (store + retrieve) without a
database, so use-case tests exercise orchestration against honest collaborators.
They are fakes, not recording mocks — assert on returned state, never on calls.
"""

from webdown.core.domain.entities.markdown_file import MarkdownFile
from webdown.core.domain.entities.markdown_file_metadata import MarkdownFileMetadata
from webdown.core.domain.entities.markdown_job import MarkdownJob
from webdown.core.domain.entities.page_conversion_status import PageConversionStatus
from webdown.core.domain.interfaces.markdown_file_repository import MarkdownFileRepository
from webdown.core.domain.interfaces.markdown_job_repository import MarkdownJobRepository
from webdown.core.domain.interfaces.page_error_repository import PageErrorRepository


class InMemoryMarkdownJobRepository(MarkdownJobRepository):
    """In-memory markdown job progress store."""

    def __init__(self) -> None:
        self._jobs: dict[str, MarkdownJob] = {}

    def create_job(self, job_id: str, total_pages: int) -> None:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        self._jobs[job_id] = MarkdownJob(
            job_id=job_id,
            status="processing",
            created_at=now,
            updated_at=now,
            total_pages=total_pages,
            processed_pages=0,
        )

    def update_job_progress(
        self,
        job_id: str,
        processed_pages: int,
        status: str = "processing",
        error_message: str | None = None,
        total_pages: int | None = None,
        failed_pages: int | None = None,
        total_available: int | None = None,
        truncated: bool | None = None,
    ) -> None:
        from datetime import datetime, timezone

        job = self._jobs[job_id]
        job.processed_pages = processed_pages
        job.status = status
        job.error_message = error_message
        if total_pages is not None:
            job.total_pages = total_pages
        if failed_pages is not None:
            job.failed_pages = failed_pages
        if total_available is not None:
            job.total_available = total_available
        if truncated is not None:
            job.truncated = truncated
        job.updated_at = datetime.now(timezone.utc).isoformat()

    def get_job_progress(self, job_id: str) -> MarkdownJob | None:
        return self._jobs.get(job_id)


class InMemoryMarkdownFileRepository(MarkdownFileRepository):
    """In-memory markdown file store."""

    def __init__(self) -> None:
        self._files: dict[str, MarkdownFile] = {}

    def save_markdown_file(self, markdown_file: MarkdownFile) -> None:
        self._files[markdown_file.job_id] = markdown_file

    def get_markdown_file(self, job_id: str) -> MarkdownFile | None:
        return self._files.get(job_id)

    def list_markdown_files(self) -> list[MarkdownFileMetadata]:
        return [
            MarkdownFileMetadata(
                id=f.id,
                job_id=f.job_id,
                created_at=f.created_at,
                ip_address=f.ip_address,
                file_size=f.file_size,
                generation_time_seconds=f.generation_time_seconds,
                status=f.status,
                base_url=f.base_url,
            )
            for f in self._files.values()
        ]


class InMemoryPageErrorRepository(PageErrorRepository):
    """In-memory per-page conversion status store."""

    def __init__(self) -> None:
        # base_url -> {url: PageConversionStatus}
        self._by_base: dict[str, dict[str, PageConversionStatus]] = {}
        # job_id -> list[PageConversionStatus]
        self._by_job: dict[str, list[PageConversionStatus]] = {}
        # job_id -> base_url (for succeeded_urls host matching)
        self._job_base: dict[str, str] = {}

    def save(self, job_id: str, status: PageConversionStatus) -> None:
        self.save_many(job_id, [status])

    def save_many(self, job_id: str, statuses: list[PageConversionStatus]) -> None:
        base_url = self._job_base.get(job_id, "")
        bucket = self._by_base.setdefault(base_url, {})
        job_list = self._by_job.setdefault(job_id, [])
        existing_urls = {s.url for s in job_list}
        for s in statuses:
            bucket[s.url] = s
            if s.url in existing_urls:
                job_list = [s if s.url == x.url else x for x in job_list]
            else:
                job_list.append(s)
                existing_urls.add(s.url)
        self._by_job[job_id] = job_list

    def register_base_url(self, job_id: str, base_url: str) -> None:
        """Test helper: record the base_url for a job (drives succeeded_urls)."""
        self._job_base[job_id] = base_url

    def get_by_job(self, job_id: str) -> list[PageConversionStatus]:
        return list(self._by_job.get(job_id, []))

    def get_successful_markdown(self, job_id: str) -> dict[str, str]:
        return {
            s.url: s.markdown
            for s in self._by_job.get(job_id, [])
            if s.status == "success" and s.markdown is not None
        }

    def succeeded_urls(self, base_url: str) -> set[str]:
        return {
            s.url
            for s in self._by_base.get(base_url, {}).values()
            if s.status == "success"
        }
