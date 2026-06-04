"""MCP tool registration."""

from webdown.presentation.mcp.tools.markdown import register_markdown_tools
from webdown.presentation.mcp.tools.rss import register_rss_tools
from webdown.presentation.mcp.tools.sitemap import register_sitemap_tools


def register_tools(server: object) -> None:
    """Register all MCP tools on the given server."""
    register_sitemap_tools(server)
    register_rss_tools(server)
    register_markdown_tools(server)
