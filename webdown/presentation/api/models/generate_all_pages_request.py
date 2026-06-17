"""API request model for generating markdown from all website pages."""

from pydantic import BaseModel, Field, HttpUrl


class GenerateAllPagesRequest(BaseModel):
    """Request model for generating markdown from all pages."""

    base_url: HttpUrl = Field(description="The base URL of the website to scrape")
    max_pages: int | None = Field(default=100, description="Maximum number of pages to convert (default 100)")
    whitelist_patterns: list[str] | None = Field(
        default=None, description="Only include URLs containing these substrings (applied first)"
    )
    blacklist_patterns: list[str] | None = Field(
        default=None, description="Exclude URLs containing these substrings (applied after whitelist)"
    )
    resume: bool = Field(
        default=False, description="Skip pages already converted successfully for this site"
    )
    capture_artifacts: bool = Field(
        default=False, description="Save crash HTML + traceback to data/debug/ for failed pages"
    )
