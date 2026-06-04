"""Domain service interface for GitHub repository processing."""

from abc import ABC, abstractmethod


class GitHubRepositoryProcessor(ABC):
    """Processes GitHub repositories into Markdown."""

    @abstractmethod
    def process_github_repository(self, repo_url: str) -> str:
        """Process a GitHub repository URL into Markdown content."""
