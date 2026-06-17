"""Use case for starting a single-page markdown generation job."""

from webdown.core.application.dto.generate_single_page_request import (
    GenerateSinglePageRequest as GenerateSinglePageRequestDto,
)
from webdown.core.application.dto.job_result import JobResult
from webdown.core.application.use_cases._job_launcher import launch_background_job
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
        return launch_background_job(
            self._job_repository,
            background_processor,
            self._generation_use_case.execute,
            total_pages=1,
            url=request.url,
            ip_address=ip_address,
        )
