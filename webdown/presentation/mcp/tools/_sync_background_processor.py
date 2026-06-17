"""Synchronous background processor for MCP tools."""

from collections.abc import Callable
from typing import Any

from webdown.core.domain.interfaces.background_processor import BackgroundProcessor


class SyncBackgroundProcessor(BackgroundProcessor):
    """Runs tasks synchronously (blocks until complete).

    Used by MCP tools that need to run generation use cases in-process
    without FastAPI's BackgroundTasks.
    """

    def submit(self, task: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        """Execute the task immediately and return an empty tracking ID.

        Synchronous execution provides no separate job ID beyond the
        application-level job_id created by the use case, so this returns
        an empty string. The caller should use the job_id returned by the
        use case itself.
        """
        task(*args, **kwargs)
        return ""
