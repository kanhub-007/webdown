"""MCP tools — web search."""

from webdown.core.application.dto.search_web_request import SearchWebRequest
from webdown.core.domain.exceptions import SearchServiceError
from webdown.startup.use_case_factory import create_search_web_use_case


def register_search_tools(server: object) -> None:
    """Register web search tools on the MCP server."""

    @server.tool(
        description=(
            "Search the web and return matching page URLs with titles and snippets. "
            "Use this to discover pages about a topic, then feed the URLs into "
            "convert_single_page or convert_all_pages to convert them to Markdown. "
            "Returns up to 20 results by default (max 50)."
        ),
    )
    def search_web(query: str, max_results: int = 20) -> dict:
        """Search the web for pages matching a query."""
        try:
            use_case = create_search_web_use_case()
            result = use_case.execute(
                SearchWebRequest(query=query, max_results=max_results)
            )
            return {
                "query": result.query,
                "results": [
                    {
                        "title": item.title,
                        "url": item.url,
                        "snippet": item.snippet,
                    }
                    for item in result.items
                ],
                "total_count": len(result.items),
            }
        except ValueError as e:
            return {"error": str(e), "query": query, "results": [], "total_count": 0}
        except SearchServiceError as e:
            return {"error": str(e), "query": query, "results": [], "total_count": 0}
