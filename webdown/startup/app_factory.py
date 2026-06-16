"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from webdown.presentation.api.routes import markdown, progress, rss, search, sitemap
from webdown.startup.repository_factory import (
    create_markdown_file_repository,
    create_markdown_job_repository,
    create_schema_initializer,
)
from webdown.startup.use_case_factory import (
    create_aggregate_rss_feeds_use_case,
    create_explore_sitemap_use_case,
    create_get_job_progress_use_case,
    create_get_markdown_file_use_case,
    create_list_markdown_files_use_case,
    create_search_web_use_case,
    create_start_all_pages_markdown_job_use_case,
    create_start_github_repo_markdown_job_use_case,
    create_start_single_page_markdown_job_use_case,
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create the main FastAPI application with mounted sub-applications."""
    _configure_logging()

    app = FastAPI(
        title="Website Documentation Tools API",
        description="""
        A suite of APIs for website documentation processing and management.

        ## Available APIs

        * **Web Index API** - Sitemap exploration and URL discovery
        * **Web Convert API** - HTML to Markdown conversion with progress tracking
        * **RSS API** - RSS feed aggregation
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        contact={"name": "API Support", "email": "support@example.com"},
        license_info={"name": "MIT"},
    )

    web_index_api = _create_sub_app(
        title="Web Index API",
        description="Sitemap exploration and URL discovery API.",
        docs_url="/docs/web-index",
        redoc_url="/redoc/web-index",
        openapi_url="/openapi/web-index.json",
    )
    web_convert_api = _create_sub_app(
        title="Web Convert API",
        description="HTML to Markdown conversion API with progress tracking.",
        docs_url="/docs/web-convert",
        redoc_url="/redoc/web-convert",
        openapi_url="/openapi/web-convert.json",
    )
    rss_api = _create_sub_app(
        title="RSS API",
        description="RSS feed aggregation API.",
        docs_url="/docs/rss",
        redoc_url="/redoc/rss",
        openapi_url="/openapi/rss.json",
    )
    for configured_app in (app, web_index_api, web_convert_api, rss_api):
        configure_application_state(configured_app)

    app.openapi = lambda: _custom_openapi(app)

    _wire_routes(app, web_index_api, web_convert_api, rss_api)
    _register_root_routes(app)
    app.state.web_index_api = web_index_api
    app.state.web_convert_api = web_convert_api
    app.state.rss_api = rss_api

    return app


def _wire_routes(app: FastAPI, web_index_api: FastAPI, web_convert_api: FastAPI, rss_api: FastAPI) -> None:
    """Register routers and mount sub-applications."""
    web_index_api.include_router(sitemap.router)
    web_index_api.include_router(search.router)
    web_convert_api.include_router(markdown.router)
    web_convert_api.include_router(progress.router)
    rss_api.include_router(rss.router)
    app.mount("/web-index", web_index_api)
    app.mount("/web-convert", web_convert_api)
    app.mount("/rss", rss_api)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize database tables on application startup."""
    create_schema_initializer().initialize()
    logger.info("Database initialized")
    logger.info("FastAPI server started")
    logger.info("Swagger UI available at: http://localhost:8000/docs")
    logger.info("ReDoc UI available at: http://localhost:8000/redoc")
    logger.info("")
    logger.info("Available APIs:")
    logger.info("  Web Index API: http://localhost:8000/web-index/docs/web-index")
    logger.info("  Web Convert API: http://localhost:8000/web-convert/docs/web-convert")
    logger.info("  RSS API: http://localhost:8000/rss/docs/rss")
    logger.info("")
    logger.info("Note: API authentication disabled - secured via Docker networking")
    yield


def configure_application_state(fastapi_app: FastAPI) -> None:
    """Attach configured dependencies to a FastAPI application."""
    fastapi_app.state.markdown_job_repository = create_markdown_job_repository()
    fastapi_app.state.markdown_file_repository = create_markdown_file_repository()
    fastapi_app.state.explore_sitemap_use_case = create_explore_sitemap_use_case()
    fastapi_app.state.aggregate_rss_feeds_use_case = create_aggregate_rss_feeds_use_case()
    fastapi_app.state.get_job_progress_use_case = create_get_job_progress_use_case()
    fastapi_app.state.get_markdown_file_use_case = create_get_markdown_file_use_case()
    fastapi_app.state.list_markdown_files_use_case = create_list_markdown_files_use_case()
    fastapi_app.state.start_all_pages_markdown_job_use_case = create_start_all_pages_markdown_job_use_case()
    fastapi_app.state.start_single_page_markdown_job_use_case = create_start_single_page_markdown_job_use_case()
    fastapi_app.state.start_github_repo_markdown_job_use_case = create_start_github_repo_markdown_job_use_case()
    fastapi_app.state.search_web_use_case = create_search_web_use_case()


def _configure_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
    )
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("webdown").setLevel(logging.DEBUG)
    logging.getLogger("webdown.infrastructure.services.beautifulsoup_html_to_markdown_converter").setLevel(
        logging.DEBUG
    )
    logger.debug("Main logger initialized at DEBUG level")


def _create_sub_app(title: str, description: str, docs_url: str, redoc_url: str, openapi_url: str) -> FastAPI:
    """Create a versioned FastAPI sub-application."""
    return FastAPI(
        title=title,
        description=description,
        version="1.0.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )


def _custom_openapi(app: FastAPI) -> dict[str, object]:
    """Customize OpenAPI schema with additional metadata."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="WebDown API",
        version="1.0.0",
        description="Convert websites to markdown format with sitemap discovery and progress tracking",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {"url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"}
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def _register_root_routes(app: FastAPI) -> None:
    """Register root-level routes."""

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Return the status of the API service."""
        return {
            "status": "healthy",
            "service": "WebDown API",
            "version": "1.0.0",
        }

    @app.get("/", tags=["Root"])
    async def root() -> dict[str, object]:
        """Return API information and documentation links."""
        return {
            "message": "Welcome to the Website Documentation Tools API",
            "version": "1.0.0",
            "apis": {
                "web_index": {
                    "description": "Sitemap exploration and URL discovery",
                    "base_url": "/web-index",
                    "documentation": {
                        "swagger": "/docs/web-index",
                        "redoc": "/redoc/web-index",
                        "openapi_schema": "/openapi/web-index.json",
                    },
                },
                "web_convert": {
                    "description": "HTML to Markdown conversion with progress tracking",
                    "base_url": "/web-convert",
                    "documentation": {
                        "swagger": "/docs/web-convert",
                        "redoc": "/redoc/web-convert",
                        "openapi_schema": "/openapi/web-convert.json",
                    },
                },
                "rss": {
                    "description": "RSS feed aggregation",
                    "base_url": "/rss",
                    "documentation": {
                        "swagger": "/docs/rss",
                        "redoc": "/redoc/rss",
                        "openapi_schema": "/openapi/rss.json",
                    },
                },
            },
            "main_documentation": {
                "swagger": "/docs",
                "redoc": "/redoc",
                "openapi_schema": "/openapi.json",
            },
        }
