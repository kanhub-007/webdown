"""GitIngest processor for converting GitHub repositories to markdown."""

import logging

from gitingest import ingest

from webdown.core.domain.interfaces.github_repository_processor import GitHubRepositoryProcessor

logger = logging.getLogger(__name__)


class GitingestGitHubRepositoryProcessor(GitHubRepositoryProcessor):
    """Processes GitHub repositories into Markdown using the gitingest library."""

    def process_github_repository(self, repo_url: str) -> str:
        """Process a GitHub repository URL into Markdown content.

        Args:
            repo_url: The GitHub repository URL (e.g. 'https://github.com/user/repo').

        Returns:
            Generated Markdown content from the repository.

        Raises:
            Exception: If the repository cannot be processed.
        """
        try:
            logger.info("Processing GitHub repository: %s", repo_url)
            summary, tree, content = ingest(repo_url)

            markdown_parts: list[str] = []
            if summary:
                markdown_parts.append(f"# Repository Summary\n\n{summary}\n")
            if tree:
                markdown_parts.append(f"# Directory Structure\n\n```\n{tree}\n```\n")
            if content:
                markdown_parts.append(f"# Repository Content\n\n{content}")

            result = "\n\n".join(markdown_parts)
            logger.info("Successfully processed repository: %s", repo_url)
            return result
        except Exception as exc:
            logger.error("Error processing GitHub repository %s: %s", repo_url, exc)
            raise Exception(f"Failed to process GitHub repository: {exc}") from exc
