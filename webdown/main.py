"""Main FastAPI application entry point.

The app singleton is created in webdown/startup/api.py (composition root).
This module is kept for backwards compatibility with uvicorn CLI usage:

    uvicorn webdown.main:app
"""

from webdown.startup.api import app, rss_api, web_convert_api, web_index_api  # noqa: F401 — re-exported for tests

__all__ = ["app", "web_index_api", "web_convert_api", "rss_api"]
