"""Use case for starting an all-pages markdown generation job."""

import uuid

from webdown.core.application.dto.generate_all_pages_request import (
    GenerateAllPagesRequest as GenerateAllPagesRequestDto,
)
from webdown.core.application.dto.job_result import JobResult
from webdown.core.application.use_cases.generate_all_pages_markdown import GenerateAllPagesMarkdownUseCase
from webdown.core.domain.interfaces.background_processor import BackgroundProcessor
from webdown.core.domain.interfaces.markdown_job_repository import MarkdownJobRepository


class StartAllPagesMarkdownJobUseCase:
    """Starts a background job that generates Markdown from all website pages."""

    def __init__(
        self,
        job_repository: MarkdownJobRepository,
        generation_use_case: GenerateAllPagesMarkdownUseCase,
    ) -> None:
        """Initialize the use case with its dependencies."""
        self._job_repository = job_repository
        self._generation_use_case = generation_use_case

    def execute(
        self,
        request: GenerateAllPagesRequestDto,
        ip_address: str,
        background_processor: BackgroundProcessor,
    ) -> JobResult:
        """Create and schedule an all-pages markdown generation job."""
        job_id = str(uuid.uuid4())
        self._job_repository.create_job(job_id, 0)
        background_processor.submit(
            self._generation_use_case.execute,
            job_id,
            request.base_url,
            request.max_pages or 1000,
            request.whitelist_patterns,
            request.blacklist_patterns,
            ip_address,
            request.resume,
        )
        return JobResult(job_id=job_id)
