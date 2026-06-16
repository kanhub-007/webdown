"""Use case factory functions."""

from functools import lru_cache

from webdown.core.application.use_cases import (
    AggregateRssFeedsUseCase,
    ExploreSitemapUseCase,
    GenerateAllPagesMarkdownUseCase,
    GenerateGitHubRepoMarkdownUseCase,
    GenerateSinglePageMarkdownUseCase,
    GetJobProgressUseCase,
    GetMarkdownFileUseCase,
    ListMarkdownFilesUseCase,
    SearchWebUseCase,
    StartAllPagesMarkdownJobUseCase,
    StartGitHubRepoMarkdownJobUseCase,
    StartSinglePageMarkdownJobUseCase,
)
from webdown.startup.repository_factory import create_markdown_file_repository, create_markdown_job_repository
from webdown.startup.service_factory import (
    create_github_repository_processor,
    create_html_to_markdown_converter,
    create_page_renderer,
    create_rss_feed_aggregator,
    create_sitemap_discovery_service,
    create_web_search_service,
)


@lru_cache(maxsize=1)
def create_explore_sitemap_use_case() -> ExploreSitemapUseCase:
    """Create the sitemap exploration use case."""
    return ExploreSitemapUseCase(create_sitemap_discovery_service())


@lru_cache(maxsize=1)
def create_aggregate_rss_feeds_use_case() -> AggregateRssFeedsUseCase:
    """Create the RSS feed aggregation use case."""
    return AggregateRssFeedsUseCase(create_rss_feed_aggregator())


@lru_cache(maxsize=1)
def create_search_web_use_case() -> SearchWebUseCase:
    """Create the web search use case."""
    return SearchWebUseCase(create_web_search_service())


@lru_cache(maxsize=1)
def create_get_job_progress_use_case() -> GetJobProgressUseCase:
    """Create the get job progress use case."""
    return GetJobProgressUseCase(create_markdown_job_repository())


@lru_cache(maxsize=1)
def create_get_markdown_file_use_case() -> GetMarkdownFileUseCase:
    """Create the get markdown file use case."""
    return GetMarkdownFileUseCase(create_markdown_file_repository())


@lru_cache(maxsize=1)
def create_list_markdown_files_use_case() -> ListMarkdownFilesUseCase:
    """Create the list markdown files use case."""
    return ListMarkdownFilesUseCase(create_markdown_file_repository())


@lru_cache(maxsize=1)
def create_generate_all_pages_markdown_use_case() -> GenerateAllPagesMarkdownUseCase:
    """Create the all-pages markdown generation use case."""
    return GenerateAllPagesMarkdownUseCase(
        create_markdown_job_repository(),
        create_markdown_file_repository(),
        create_sitemap_discovery_service(),
        create_page_renderer(),
        create_html_to_markdown_converter(),
    )


@lru_cache(maxsize=1)
def create_generate_single_page_markdown_use_case() -> GenerateSinglePageMarkdownUseCase:
    """Create the single-page markdown generation use case."""
    return GenerateSinglePageMarkdownUseCase(
        create_markdown_job_repository(),
        create_markdown_file_repository(),
        create_page_renderer(),
        create_html_to_markdown_converter(),
    )


@lru_cache(maxsize=1)
def create_generate_github_repo_markdown_use_case() -> GenerateGitHubRepoMarkdownUseCase:
    """Create the GitHub repository markdown generation use case."""
    return GenerateGitHubRepoMarkdownUseCase(
        create_markdown_job_repository(),
        create_markdown_file_repository(),
        create_github_repository_processor(),
    )


@lru_cache(maxsize=1)
def create_start_all_pages_markdown_job_use_case() -> StartAllPagesMarkdownJobUseCase:
    """Create the all-pages markdown job starter use case."""
    return StartAllPagesMarkdownJobUseCase(
        create_markdown_job_repository(),
        create_generate_all_pages_markdown_use_case(),
    )


@lru_cache(maxsize=1)
def create_start_single_page_markdown_job_use_case() -> StartSinglePageMarkdownJobUseCase:
    """Create the single-page markdown job starter use case."""
    return StartSinglePageMarkdownJobUseCase(
        create_markdown_job_repository(),
        create_generate_single_page_markdown_use_case(),
    )


@lru_cache(maxsize=1)
def create_start_github_repo_markdown_job_use_case() -> StartGitHubRepoMarkdownJobUseCase:
    """Create the GitHub repository markdown job starter use case."""
    return StartGitHubRepoMarkdownJobUseCase(
        create_markdown_job_repository(),
        create_generate_github_repo_markdown_use_case(),
    )
