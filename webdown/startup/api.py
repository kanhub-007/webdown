"""API startup — app singleton and uvicorn runner.

Clean architecture: this startup module creates the FastAPI app singleton
and provides the CLI runner. The presentation/ layer only declares routes.
"""

import os

from dotenv import load_dotenv

from webdown.startup.app_factory import create_app

load_dotenv()

app = create_app()
web_index_api = app.state.web_index_api
web_convert_api = app.state.web_convert_api
rss_api = app.state.rss_api


def run() -> None:
    """Start the uvicorn server. Called by CLI entry points."""
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "").lower() in ("1", "true", "yes")

    uvicorn.run(
        "webdown.startup.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="debug",
    )
