"""Thread-based background processor for MCP tools that need non-blocking execution."""

import threading
from collections.abc import Callable
from typing import Any

from webdown.core.domain.interfaces.background_processor import BackgroundProcessor


class ThreadBackgroundProcessor(BackgroundProcessor):
    """Runs tasks in a daemon thread (does not block the caller).

    Used by MCP tools for long-running operations like convert_all_pages
    where the caller should get an immediate job_id and poll for progress.
    """

    def submit(self, task: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Submit the task to a daemon thread (does not block the caller)."""
        thread = threading.Thread(target=task, args=args, kwargs=kwargs, daemon=True, name="mcp-bg-job")
        thread.start()
