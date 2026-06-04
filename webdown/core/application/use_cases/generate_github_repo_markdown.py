"""Use case for generating markdown from a GitHub repository."""

import logging
import time
from datetime import datetime, timezone

from webdown.core.domain.entities.markdown_file import MarkdownFile
from webdown.core.domain.entities.sitemap_url import SitemapUrl
from webdown.core.domain.interfaces.github_repository_processor import GitHubRepositoryProcessor
from webdown.core.domain.interfaces.markdown_file_repository import MarkdownFileRepository
from webdown.core.domain.interfaces.markdown_job_repository import MarkdownJobRepository

logger = logging.getLogger(__name__)


class GenerateGitHubRepoMarkdownUseCase:
    """Generates Markdown from a GitHub repository."""

    def __init__(
        self,
        job_repository: MarkdownJobRepository,
        file_repository: MarkdownFileRepository,
        github_repository_processor: GitHubRepositoryProcessor,
    ) -> None:
        """Initialize the use case with its dependencies."""
        self._job_repository = job_repository
        self._file_repository = file_repository
        self._github_repository_processor = github_repository_processor

    def execute(self, job_id: str, repo_url: str, ip_address: str) -> None:
        """Generate Markdown from a GitHub repository."""
        start_time = time.time()

        try:
            markdown = self._github_repository_processor.process_github_repository(repo_url)
            if not markdown or not markdown.strip():
                raise RuntimeError("Conversion resulted in empty markdown content")

            self._file_repository.save_markdown_file(
                MarkdownFile(
                    job_id=job_id,
                    content=markdown,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    ip_address=ip_address,
                    file_size=len(markdown.encode("utf-8")),
                    generation_time_seconds=time.time() - start_time,
                    base_url=repo_url,
                    sitemap_urls=[SitemapUrl(loc=repo_url)],
                )
            )
            self._job_repository.update_job_progress(job_id, 1, "completed")
        except Exception as error:
            logger.error(f"Error generating markdown for GitHub repo {repo_url}: {error}", exc_info=True)
            self._job_repository.update_job_progress(job_id, 0, "failed", str(error))
