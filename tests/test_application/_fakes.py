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
from webdown.core.domain.services.url_normalizer import normalize_host


class InMemoryMarkdownJobRepository(MarkdownJobRepository):
    """In-memory markdown job progress store."""

    def __init__(self) -> None:
        self._jobs: dict[str, MarkdownJob] = {}

    def create_job(self, job_id: str, total_pages: int) -> None:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
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
        job.updated_at = datetime.now(timezone.utc)

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

    def list_markdown_files(self, limit: int = 100, offset: int = 0) -> list[MarkdownFileMetadata]:
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
    """In-memory per-page conversion status store (host-keyed, like SQLite)."""

    def __init__(self) -> None:
        # job_id -> list[PageConversionStatus] (insertion-ordered, deduped by url)
        self._by_job: dict[str, list[PageConversionStatus]] = {}

    def save(self, job_id: str, status: PageConversionStatus) -> None:
        self.save_many(job_id, [status])

    def save_many(self, job_id: str, statuses: list[PageConversionStatus]) -> None:
        job_list = self._by_job.setdefault(job_id, [])
        existing_urls = {s.url for s in job_list}
        for s in statuses:
            if s.url in existing_urls:
                job_list = [(s if s.url == x.url else x) for x in job_list]
            else:
                job_list.append(s)
                existing_urls.add(s.url)
        self._by_job[job_id] = job_list

    def get_by_job(self, job_id: str) -> list[PageConversionStatus]:
        return list(self._by_job.get(job_id, []))

    def _all_statuses(self):
        for lst in self._by_job.values():
            yield from lst

    def get_successful_markdown(self, job_id: str) -> dict[str, str]:
        return {
            s.url: s.markdown
            for s in self._by_job.get(job_id, [])
            if s.status == "success" and s.markdown is not None
        }

    def succeeded_urls(self, base_url: str) -> set[str]:
        host = normalize_host(base_url)
        return {
            s.url for s in self._all_statuses()
            if s.status == "success" and normalize_host(s.url) == host
        }

    def get_successful_markdown_by_base(self, base_url: str) -> dict[str, str]:
        host = normalize_host(base_url)
        return {
            s.url: s.markdown
            for s in self._all_statuses()
            if s.status == "success" and s.markdown is not None and normalize_host(s.url) == host
        }
