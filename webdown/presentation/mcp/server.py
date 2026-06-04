"""MCP server — FastMCP server creation and tool registration."""

from webdown.presentation.mcp.tools import register_tools


def create_server() -> object:
    """Build the FastMCP server with all tools registered."""
    from fastmcp import FastMCP

    server = FastMCP(
        name="webdown",
        instructions=(
            "WebDown converts websites and GitHub repositories to Markdown, "
            "explores sitemaps, and aggregates RSS feeds.\n\n"
            "FIRST: call get_usage_guide() for a comprehensive guide.\n\n"
            "QUICK REFERENCE:\n"
            "• explore_sitemap(base_url) — discover all pages on a website\n"
            "• convert_single_page(url) — convert one page to Markdown\n"
            "• convert_all_pages(base_url) — convert entire website to Markdown\n"
            "• convert_github_repo(repo_url) — convert a GitHub repo to Markdown\n"
            "• aggregate_rss_feeds() — get latest crypto/AI news\n"
            "• get_job_progress(job_id) — check conversion progress\n"
            "• download_markdown(job_id) — get the generated Markdown\n"
            "• list_markdown_files() — see all previously generated files"
        ),
    )

    register_tools(server)
    return server
