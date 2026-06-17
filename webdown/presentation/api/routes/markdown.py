"""
Markdown generation and management endpoints.
"""

from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from webdown.core.application.dto.generate_all_pages_request import (
    GenerateAllPagesRequest as GenerateAllPagesRequestDto,
)
from webdown.core.application.dto.generate_github_repo_request import (
    GenerateGitHubRepoRequest as GenerateGitHubRepoRequestDto,
)
from webdown.core.application.dto.generate_single_page_request import (
    GenerateSinglePageRequest as GenerateSinglePageRequestDto,
)
from webdown.core.application.dto.markdown_file_metadata_result import MarkdownFileMetadataResult
from webdown.core.application.use_cases import (
    GetMarkdownFileUseCase,
    ListMarkdownFilesUseCase,
    StartAllPagesMarkdownJobUseCase,
    StartGitHubRepoMarkdownJobUseCase,
    StartSinglePageMarkdownJobUseCase,
)
from webdown.presentation.api.adapters.fastapi_background_processor import FastApiBackgroundProcessor
from webdown.presentation.api.models import (
    GenerateAllPagesRequest,
    GenerateGitHubRepoRequest,
    GenerateSinglePageRequest,
    JobResponse,
    MarkdownFileMetadata,
)
from webdown.presentation.api.presenters.job_presenter import JobPresenter
from webdown.presentation.api.presenters.markdown_presenter import MarkdownPresenter

router = APIRouter(prefix="/api/markdown", tags=["Markdown Conversion"])


def get_start_all_pages_markdown_job_use_case(request: Request) -> StartAllPagesMarkdownJobUseCase:
    return request.app.state.start_all_pages_markdown_job_use_case


def get_start_single_page_markdown_job_use_case(request: Request) -> StartSinglePageMarkdownJobUseCase:
    return request.app.state.start_single_page_markdown_job_use_case


def get_start_github_repo_markdown_job_use_case(request: Request) -> StartGitHubRepoMarkdownJobUseCase:
    return request.app.state.start_github_repo_markdown_job_use_case


def get_markdown_file_use_case(request: Request) -> GetMarkdownFileUseCase:
    return request.app.state.get_markdown_file_use_case


def get_list_markdown_files_use_case(request: Request) -> ListMarkdownFilesUseCase:
    return request.app.state.list_markdown_files_use_case


def get_job_presenter() -> JobPresenter:
    return JobPresenter()


def get_markdown_presenter() -> MarkdownPresenter:
    return MarkdownPresenter()


@router.post("/generate-all", response_model=JobResponse)
async def generate_markdown_all_pages(
    request: GenerateAllPagesRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    use_case: StartAllPagesMarkdownJobUseCase = Depends(get_start_all_pages_markdown_job_use_case),
    presenter: JobPresenter = Depends(get_job_presenter),
):
    """Convert all pages from a website sitemap into a single Markdown file.

    Discovers pages via sitemap, applies optional whitelist/blacklist URL filters,
    renders each page with Playwright, converts HTML to Markdown, and combines
    everything into one file. Runs in the background — use get_job_progress to
    track and download to retrieve the result.
    """
    dto = GenerateAllPagesRequestDto(
        base_url=str(request.base_url),
        max_pages=request.max_pages,
        whitelist_patterns=request.whitelist_patterns,
        blacklist_patterns=request.blacklist_patterns,
        resume=request.resume,
        capture_artifacts=request.capture_artifacts,
    )
    result = use_case.execute(
        request=dto,
        ip_address=http_request.client.host,
        background_processor=FastApiBackgroundProcessor(background_tasks),
    )
    return presenter.to_response(result)


@router.post("/generate-single", response_model=JobResponse)
async def generate_markdown_single_page(
    request: GenerateSinglePageRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    use_case: StartSinglePageMarkdownJobUseCase = Depends(get_start_single_page_markdown_job_use_case),
    presenter: JobPresenter = Depends(get_job_presenter),
):
    """Convert a single web page to Markdown.

    Renders the page with Playwright (including JavaScript), converts HTML to
    Markdown preserving headings, tables, code blocks, and alerts. Runs in the
    background — use get_job_progress to track and download to retrieve.
    """
    dto = GenerateSinglePageRequestDto(url=str(request.url))
    result = use_case.execute(
        request=dto,
        ip_address=http_request.client.host,
        background_processor=FastApiBackgroundProcessor(background_tasks),
    )
    return presenter.to_response(result)


@router.get("/download/{job_id}")
async def download_markdown(
    job_id: str,
    use_case: GetMarkdownFileUseCase = Depends(get_markdown_file_use_case),
):
    """Download generated Markdown content by job ID.

    Returns the full Markdown file as a downloadable attachment. The filename
    is derived from the original website domain.
    """
    markdown_file = use_case.execute(job_id)
    if not markdown_file:
        raise HTTPException(status_code=404, detail="Markdown file not found")
    domain = urlparse(markdown_file.base_url).netloc or "page"
    return Response(
        content=markdown_file.content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{domain}_{job_id[:8]}.md"'},
    )


@router.get("/list")
async def list_generated_files(
    use_case: ListMarkdownFilesUseCase = Depends(get_list_markdown_files_use_case),
    presenter: MarkdownPresenter = Depends(get_markdown_presenter),
):
    """List all generated markdown files.

    Returns metadata for every file (job_id, created_at, base_url, file_size,
    status) without the content. Use to find old conversions before downloading.
    """
    result = use_case.execute()
    response = presenter.metadata_list_to_response(result)
    return JSONResponse(content=response)


@router.get("/metadata/{job_id}", response_model=MarkdownFileMetadata)
async def get_file_metadata(
    job_id: str,
    use_case: GetMarkdownFileUseCase = Depends(get_markdown_file_use_case),
    presenter: MarkdownPresenter = Depends(get_markdown_presenter),
):
    """Get detailed metadata for a specific markdown file.

    Returns job_id, timestamps, file size, generation time, base URL, and the
    full list of sitemap URLs that were processed.
    """
    markdown_file = use_case.execute(job_id)
    if not markdown_file:
        raise HTTPException(status_code=404, detail="Markdown file not found")
    sitemap_urls = [{"loc": url.loc, "lastmod": url.lastmod} for url in markdown_file.sitemap_urls]
    metadata = MarkdownFileMetadataResult(
        job_id=markdown_file.job_id,
        created_at=markdown_file.created_at,
        ip_address=markdown_file.ip_address,
        file_size=markdown_file.file_size,
        generation_time_seconds=markdown_file.generation_time_seconds,
        base_url=markdown_file.base_url,
        status=markdown_file.status,
        id=markdown_file.id,
    )
    return presenter.to_pydantic_metadata(metadata=metadata, sitemap_urls=sitemap_urls)


@router.post("/generate-github-repo", response_model=JobResponse)
async def generate_markdown_github_repo(
    request: GenerateGitHubRepoRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    use_case: StartGitHubRepoMarkdownJobUseCase = Depends(get_start_github_repo_markdown_job_use_case),
    presenter: JobPresenter = Depends(get_job_presenter),
):
    """Convert a GitHub repository to Markdown.

    Extracts README, source files, and directory structure into a single
    Markdown document. Runs in the background — use get_job_progress to track.
    """
    dto = GenerateGitHubRepoRequestDto(repo_url=str(request.repo_url))
    result = use_case.execute(
        request=dto,
        ip_address=http_request.client.host,
        background_processor=FastApiBackgroundProcessor(background_tasks),
    )
    return presenter.to_response(result)
