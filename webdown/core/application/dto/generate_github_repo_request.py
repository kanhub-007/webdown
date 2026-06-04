"""Application DTO for GitHub repository markdown generation request."""

from dataclasses import dataclass


@dataclass
class GenerateGitHubRepoRequest:
    """Request data for generating markdown from a GitHub repository."""

    repo_url: str
