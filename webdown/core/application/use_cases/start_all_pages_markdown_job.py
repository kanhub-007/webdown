"""Use case for starting an all-pages markdown generation job."""

from webdown.core.application.dto.generate_all_pages_request import (
    GenerateAllPagesRequest as GenerateAllPagesRequestDto,
)
from webdown.core.application.dto.job_result import JobResult
from webdown.core.application.use_cases._job_launcher import launch_background_job
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
        return launch_background_job(
            self._job_repository,
            background_processor,
            self._generation_use_case.execute,
            total_pages=0,
            base_url=request.base_url,
            max_pages=request.max_pages or 1000,
            whitelist_patterns=request.whitelist_patterns,
            blacklist_patterns=request.blacklist_patterns,
            ip_address=ip_address,
            resume=request.resume,
            capture_artifacts=request.capture_artifacts,
        )
