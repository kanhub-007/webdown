"""MCP tools — sitemap exploration."""

from webdown.core.application.dto.sitemap_explore_request import SitemapExploreRequest
from webdown.startup.use_case_factory import create_explore_sitemap_use_case


def register_sitemap_tools(server: object) -> None:
    """Register sitemap exploration tools on the MCP server."""

    @server.tool(
        description=(
            "Discover all pages from a website's sitemap. "
            "Use this BEFORE converting pages — it shows you what pages exist "
            "so you can decide which ones to convert. "
            "Returns URLs with metadata (last modified, change frequency, priority) "
            "and the sitemap files that were visited."
        ),
    )
    def explore_sitemap(base_url: str, max_pages: int = 100) -> dict:
        """Discover all pages from a website's sitemap."""
        use_case = create_explore_sitemap_use_case()
        result = use_case.execute(SitemapExploreRequest(base_url=base_url, max_pages=max_pages))
        return {
            "pages": [
                {"loc": page.loc, "lastmod": page.lastmod, "changefreq": page.changefreq, "priority": page.priority}
                for page in result.pages
            ],
            "sitemap_files_visited": result.sitemap_files_visited,
            "total_count": len(result.pages),
        }
