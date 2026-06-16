"""Application use cases."""

from webdown.core.application.use_cases.aggregate_rss_feeds import AggregateRssFeedsUseCase
from webdown.core.application.use_cases.explore_sitemap import ExploreSitemapUseCase
from webdown.core.application.use_cases.generate_all_pages_markdown import GenerateAllPagesMarkdownUseCase
from webdown.core.application.use_cases.generate_github_repo_markdown import GenerateGitHubRepoMarkdownUseCase
from webdown.core.application.use_cases.generate_single_page_markdown import GenerateSinglePageMarkdownUseCase
from webdown.core.application.use_cases.get_job_progress import GetJobProgressUseCase
from webdown.core.application.use_cases.get_markdown_file import GetMarkdownFileUseCase
from webdown.core.application.use_cases.list_markdown_files import ListMarkdownFilesUseCase
from webdown.core.application.use_cases.save_markdown_to_file import SaveMarkdownToFileUseCase
from webdown.core.application.use_cases.start_all_pages_markdown_job import StartAllPagesMarkdownJobUseCase
from webdown.core.application.use_cases.start_github_repo_markdown_job import StartGitHubRepoMarkdownJobUseCase
from webdown.core.application.use_cases.search_web import SearchWebUseCase
from webdown.core.application.use_cases.start_single_page_markdown_job import StartSinglePageMarkdownJobUseCase

__all__ = [
    "AggregateRssFeedsUseCase",
    "ExploreSitemapUseCase",
    "GenerateAllPagesMarkdownUseCase",
    "GenerateGitHubRepoMarkdownUseCase",
    "GenerateSinglePageMarkdownUseCase",
    "GetJobProgressUseCase",
    "GetMarkdownFileUseCase",
    "ListMarkdownFilesUseCase",
    "SaveMarkdownToFileUseCase",
    "SearchWebUseCase",
    "StartAllPagesMarkdownJobUseCase",
    "StartGitHubRepoMarkdownJobUseCase",
    "StartSinglePageMarkdownJobUseCase",
]
