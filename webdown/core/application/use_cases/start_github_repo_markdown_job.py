"""Use case for starting a GitHub repository markdown generation job."""

from webdown.core.application.dto.generate_github_repo_request import (
    GenerateGitHubRepoRequest as GenerateGitHubRepoRequestDto,
)
from webdown.core.application.dto.job_result import JobResult
from webdown.core.application.use_cases._job_launcher import launch_background_job
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
        return launch_background_job(
            self._job_repository,
            background_processor,
            self._generation_use_case.execute,
            total_pages=1,
            repo_url=request.repo_url,
            ip_address=ip_address,
        )
