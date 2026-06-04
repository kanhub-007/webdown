"""API request model for generating markdown from a GitHub repository."""

from pydantic import BaseModel, Field, HttpUrl


class GenerateGitHubRepoRequest(BaseModel):
    """Request model for generating markdown from a GitHub repository."""

    repo_url: HttpUrl = Field(description="The GitHub repository URL (e.g., https://github.com/user/repo)")
