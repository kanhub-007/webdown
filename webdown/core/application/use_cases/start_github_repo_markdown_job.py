"""Use case for starting a GitHub repository markdown generation job."""

import uuid

from webdown.core.application.dto.generate_github_repo_request import (
    GenerateGitHubRepoRequest as GenerateGitHubRepoRequestDto,
)
from webdown.core.application.dto.job_result import JobResult
from webdown.core.application.use_cases.generate_github_repo_markdown import GenerateGitHubRepoMarkdownUseCase
from webdown.core.domain.interfaces.background_processor import BackgroundProcessor
from webdown.core.domain.interfaces.markdown_job_repository import MarkdownJobRepository


class StartGitHubRepoMarkdownJobUseCase:
    """Starts a background job that generates Markdown from a GitHub repository."""

    def __init__(
        self,
        job_repository: MarkdownJobRepository,
        generation_use_case: GenerateGitHubRepoMarkdownUseCase,
    ) -> None:
        """Initialize the use case with its dependencies."""
        self._job_repository = job_repository
        self._generation_use_case = generation_use_case

    def execute(
        self,
        request: GenerateGitHubRepoRequestDto,
        ip_address: str,
        background_processor: BackgroundProcessor,
    ) -> JobResult:
        """Create and schedule a GitHub repository markdown generation job."""
        job_id = str(uuid.uuid4())
        self._job_repository.create_job(job_id, 1)
        background_processor.submit(self._generation_use_case.execute, job_id, request.repo_url, ip_address)
        return JobResult(job_id=job_id)
