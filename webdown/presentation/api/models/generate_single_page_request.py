"""API request model for generating markdown from a single page."""

from pydantic import BaseModel, Field, HttpUrl


class GenerateSinglePageRequest(BaseModel):
    """Request model for generating markdown from a single page."""

    url: HttpUrl = Field(description="The URL of the page to convert to Markdown")
