"""MCP tools — markdown generation and management."""

import uuid

from webdown.core.application.dto.generate_all_pages_request import GenerateAllPagesRequest
from webdown.core.application.dto.generate_github_repo_request import GenerateGitHubRepoRequest
from webdown.core.application.dto.generate_single_page_request import GenerateSinglePageRequest
from webdown.presentation.mcp.tools._sync_background_processor import SyncBackgroundProcessor
from webdown.presentation.mcp.tools._thread_background_processor import ThreadBackgroundProcessor
from webdown.startup.use_case_factory import (
    create_get_job_progress_use_case,
    create_get_markdown_file_use_case,
    create_list_markdown_files_use_case,
    create_save_markdown_to_file_use_case,
    create_start_all_pages_markdown_job_use_case,
    create_start_github_repo_markdown_job_use_case,
    create_start_single_page_markdown_job_use_case,
)


def _usage_guide_text() -> str:
    """Return the full usage guide for AI assistants."""
    return (
        "WEB DIGEST — Usage Guide for AI Assistants\n"
        "===========================================\n\n"
        "WebDown converts websites and GitHub repositories to Markdown, "
        "explores sitemaps, searches the web, and aggregates RSS feeds.\n\n"
        "TYPICAL WORKFLOW\n"
        "  1. search_web(query) — discover relevant URLs for a topic\n"
        "  2. explore_sitemap(base_url) — see what pages exist on a website\n"
        "  3. convert_single_page(url) — convert one page to Markdown (fast, synchronous)\n"
        "     OR convert_all_pages(base_url) — convert the entire site (for large sites)\n"
        "  4. get_job_progress(job_id) — track conversion progress\n"
        "  5. download_markdown(job_id) — get the generated Markdown content\n"
        "  6. save_markdown_to_file(job_id) — write Markdown to a .md FILE, return path+size\n"
        "     (prefer over download_markdown for large conversions)\n"
        "  7. list_markdown_files() — see all previously generated files\n\n"
        "TOOLS REFERENCE\n"
        "  search_web(query, max_results=20)\n"
        "    Search the web and return page URLs with titles and snippets.\n"
        "    Use this to discover URLs, then feed them into convert_single_page.\n\n"
        "  explore_sitemap(base_url, max_pages=100)\n"
        "    Discover all pages from a website sitemap. Call this FIRST before converting.\n"
        "    Returns a list of page URLs with metadata.\n\n"
        "  convert_single_page(url)\n"
        "    Convert ONE page to Markdown. Fast, synchronous — returns immediately.\n"
        "    Best for: reading documentation, extracting specific pages.\n\n"
        "  convert_all_pages(base_url, max_pages=100, whitelist, blacklist)\n"
        "    Convert EVERY page from a sitemap into one combined Markdown file.\n"
        "    Runs synchronously (blocks until done). For large sites, this may take time.\n"
        "    Use whitelist/blacklist as comma-separated URL patterns to filter.\n"
        "    Best for: downloading entire documentation sites.\n\n"
        "  convert_github_repo(repo_url)\n"
        "    Convert a GitHub repository to Markdown. Fast, synchronous.\n"
        "    Best for: reading codebase documentation, README, source files.\n\n"
        "  get_job_progress(job_id)\n"
        "    Check how a conversion is progressing. Returns status, total/processed pages.\n\n"
        "  download_markdown(job_id)\n"
        "    Get the full Markdown content of a completed conversion.\n\n"
        "  save_markdown_to_file(job_id, output_path=None, split_per_page=False)\n"
        "    Write a completed conversion to a .md FILE on disk; return {path, size_bytes}.\n"
        "    Use this (not download_markdown) for large conversions to avoid huge responses.\n\n"
        "  list_markdown_files()\n"
        "    See all previously generated files (metadata only, no content).\n\n"
        "  aggregate_rss_feeds(published_after=None)\n"
        "    Get latest news from crypto/AI sources. Use published_after for date filter.\n\n"
        "  generate_job_id()\n"
        "    Generate a unique ID for tracking manual operations.\n\n"
        "BEST PRACTICES\n"
        "  • Use search_web() to discover URLs for a topic you want to learn about.\n"
        "  • Always explore_sitemap() first to see what pages exist on a website.\n"
        "  • Use convert_single_page() for single pages, convert_all_pages() for whole sites.\n"
        "  • For GitHub, use convert_github_repo() directly — no sitemap needed.\n"
        "  • Track progress with get_job_progress() if conversion takes time.\n"
        "  • Downloaded markdown includes headings, tables, code blocks, and alerts.\n"
        "  • Generated files persist in SQLite — use list_markdown_files() to find old conversions.\n"
        "  • Call this guide again anytime: get_usage_guide()\n"
    )


def register_markdown_tools(server: object) -> None:
    """Register markdown generation and management tools on the MCP server."""

    @server.tool(description="Return a comprehensive usage guide. Call this FIRST if you are new to WebDown.")
    def get_usage_guide() -> str:
        """Return the full usage guide explaining all tools and best practices."""
        return _usage_guide_text()

    @server.tool(
        description=(
            "Convert ONE web page to Markdown. Fast and synchronous — returns immediately. "
            "Use this for reading documentation or extracting specific pages. "
            "For full sites, use convert_all_pages instead."
        ),
    )
    def convert_single_page(url: str) -> dict:
        """Convert a single web page to Markdown synchronously."""
        use_case = create_start_single_page_markdown_job_use_case()
        result = use_case.execute(
            request=GenerateSinglePageRequest(url=url),
            ip_address="mcp",
            background_processor=SyncBackgroundProcessor(),
        )
        return {"job_id": result.job_id, "status": "completed", "message": result.message}

    @server.tool(
        description=(
            "Convert a GitHub repository to Markdown. Fast and synchronous. "
            "Extracts README, source files, and directory structure. "
            "Use for reading codebase documentation and source code."
        ),
    )
    def convert_github_repo(repo_url: str) -> dict:
        """Convert a GitHub repository to Markdown synchronously."""
        use_case = create_start_github_repo_markdown_job_use_case()
        result = use_case.execute(
            request=GenerateGitHubRepoRequest(repo_url=repo_url),
            ip_address="mcp",
            background_processor=SyncBackgroundProcessor(),
        )
        return {"job_id": result.job_id, "status": "completed", "message": result.message}

    @server.tool(
        description=(
            "Convert EVERY page from a website sitemap into one combined Markdown file. "
            "Runs synchronously (blocks until complete). "
            "Use whitelist_patterns (comma-separated URL substrings to include) "
            "and blacklist_patterns (comma-separated URL substrings to exclude) to filter pages. "
            "Track progress with get_job_progress, then download with download_markdown."
        ),
    )
    def convert_all_pages(
        base_url: str,
        max_pages: int = 1000,
        whitelist_patterns: str | None = None,
        blacklist_patterns: str | None = None,
    ) -> dict:
        """Convert all pages from a website sitemap to Markdown."""
        whitelist = [p.strip() for p in whitelist_patterns.split(",") if p.strip()] if whitelist_patterns else None
        blacklist = [p.strip() for p in blacklist_patterns.split(",") if p.strip()] if blacklist_patterns else None

        use_case = create_start_all_pages_markdown_job_use_case()
        result = use_case.execute(
            request=GenerateAllPagesRequest(
                base_url=base_url,
                max_pages=max_pages,
                whitelist_patterns=whitelist,
                blacklist_patterns=blacklist,
            ),
            ip_address="mcp",
            background_processor=ThreadBackgroundProcessor(),
        )
        return {"job_id": result.job_id, "status": "processing", "message": result.message}

    @server.tool(
        description=(
            "Check the progress of a markdown generation job. "
            "Returns status (processing/completed/failed), total pages, pages processed, "
            "and any error message. Poll this after starting a conversion."
        ),
    )
    def get_job_progress(job_id: str) -> dict:
        """Check the progress of a markdown generation job."""
        result = create_get_job_progress_use_case().execute(job_id)
        if result is None:
            return {"error": "Job not found", "job_id": job_id}
        return {
            "job_id": result.job_id,
            "status": result.status,
            "total_pages": result.total_pages,
            "processed_pages": result.processed_pages,
            "failed_pages": result.failed_pages,
            "total_available": result.total_available,
            "truncated": result.truncated,
            "error_message": result.error_message,
        }

    @server.tool(
        description=(
            "Download completed Markdown content by job ID. "
            "Returns the full Markdown text plus metadata (file size, base URL). "
            "The content can be large — it contains the entire converted website or repository."
        ),
    )
    def download_markdown(job_id: str) -> dict:
        """Download a completed markdown file by job ID."""
        result = create_get_markdown_file_use_case().execute(job_id)
        if result is None:
            return {"error": "File not found", "job_id": job_id}
        return {
            "job_id": job_id,
            "base_url": result.base_url,
            "content": result.content,
            "file_size": result.file_size,
        }

    @server.tool(
        description=(
            "List all previously generated markdown files. "
            "Returns metadata only (job_id, created_at, base_url, file_size, status) — no content. "
            "Use this to find old conversions before downloading them."
        ),
    )
    def list_markdown_files() -> dict:
        """List all generated markdown files (metadata only, no content)."""
        files = create_list_markdown_files_use_case().execute()
        return {
            "files": [
                {
                    "job_id": f.job_id,
                    "created_at": f.created_at,
                    "base_url": f.base_url,
                    "file_size": f.file_size,
                    "status": f.status,
                }
                for f in files
            ],
            "total": len(files),
        }

    @server.tool(
        description=(
            "Save a completed conversion's Markdown to a .md FILE on disk and return only "
            "the path and byte size (not the content). Use this instead of download_markdown "
            "for large conversions to avoid shipping megabytes through the response. "
            "output_path defaults to data/output/{job_id}.md. Set split_per_page=True to write "
            "one .md per successful page into output_path (a directory)."
        ),
    )
    def save_markdown_to_file(
        job_id: str,
        output_path: str | None = None,
        split_per_page: bool = False,
    ) -> dict:
        """Write a stored markdown conversion to disk; return {path, size_bytes}."""
        from webdown.core.application.dto.save_markdown_to_file_request import SaveMarkdownToFileRequest
        from webdown.core.domain.exceptions import MarkdownFileNotFoundError

        use_case = create_save_markdown_to_file_use_case()
        try:
            result = use_case.execute(
                SaveMarkdownToFileRequest(
                    job_id=job_id,
                    output_path=output_path,
                    split_per_page=split_per_page,
                )
            )
        except MarkdownFileNotFoundError:
            return {"error": "File not found", "job_id": job_id}
        return {
            "job_id": job_id,
            "path": result.path,
            "size_bytes": result.size_bytes,
            "pages_written": result.pages_written,
        }

    @server.tool(description="Generate a unique job ID for tracking manual conversion operations.")
    def generate_job_id() -> dict:
        """Generate a unique job ID for tracking."""
        return {"job_id": str(uuid.uuid4())}
