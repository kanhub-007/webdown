"""Use case for starting a single-page markdown generation job."""

import uuid

from webdown.core.application.dto.generate_single_page_request import (
    GenerateSinglePageRequest as GenerateSinglePageRequestDto,
)
from webdown.core.application.dto.job_result import JobResult
from webdown.core.application.use_cases.generate_single_page_markdown import GenerateSinglePageMarkdownUseCase
from webdown.core.domain.interfaces.background_processor import BackgroundProcessor
from webdown.core.domain.interfaces.markdown_job_repository import MarkdownJobRepository


class StartSinglePageMarkdownJobUseCase:
    """Starts a background job that generates Markdown from one web page."""

    def __init__(
        self,
        job_repository: MarkdownJobRepository,
        generation_use_case: GenerateSinglePageMarkdownUseCase,
    ) -> None:
        """Initialize the use case with its dependencies."""
        self._job_repository = job_repository
        self._generation_use_case = generation_use_case

    def execute(
        self,
        request: GenerateSinglePageRequestDto,
        ip_address: str,
        background_processor: BackgroundProcessor,
    ) -> JobResult:
        """Create and schedule a single-page markdown generation job."""
        job_id = str(uuid.uuid4())
        self._job_repository.create_job(job_id, 1)
        background_processor.submit(self._generation_use_case.execute, job_id, request.url, ip_address)
        return JobResult(job_id=job_id)
