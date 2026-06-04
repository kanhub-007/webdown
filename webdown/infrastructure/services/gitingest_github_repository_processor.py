"""
GitIngest processor for converting GitHub repositories to markdown.

This module uses the gitingest package to process GitHub repositories
and generate comprehensive markdown documentation.
"""

import logging
from gitingest import ingest

from webdown.core.domain.interfaces.github_repository_processor import GitHubRepositoryProcessor

logger = logging.getLogger(__name__)


def process_github_repository(repo_url: str) -> str:
    """
    Process a GitHub repository URL and generate markdown documentation.

    Args:
        repo_url: The GitHub repository URL (e.g., 'https://github.com/user/repo')

    Returns:
        str: Generated markdown content from the repository

    Raises:
        Exception: If the repository cannot be processed
    """
    try:
        logger.info(f"Processing GitHub repository: {repo_url}")

        summary, tree, content = ingest(repo_url)

        # Combine summary, tree, and content into a comprehensive markdown
        markdown_parts = []

        # Add summary if available
        if summary:
            markdown_parts.append(f"# Repository Summary\n\n{summary}\n")

        # Add directory tree if available
        if tree:
            markdown_parts.append(f"# Directory Structure\n\n```\n{tree}\n```\n")

        # Add content
        if content:
            markdown_parts.append(f"# Repository Content\n\n{content}")

        result = "\n\n".join(markdown_parts)
        logger.info(f"Successfully processed repository: {repo_url}")

        return result

    except Exception as e:
        logger.error(f"Error processing GitHub repository {repo_url}: {e}")
        raise Exception(f"Failed to process GitHub repository: {str(e)}")


class GitingestGitHubRepositoryProcessor(GitHubRepositoryProcessor):
    """GitHub repository processor backed by gitingest."""

    def process_github_repository(self, repo_url: str) -> str:
        """Process a GitHub repository URL into Markdown content."""
        return process_github_repository(repo_url)
