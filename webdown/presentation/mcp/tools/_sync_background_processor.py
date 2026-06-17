"""Synchronous background processor for MCP tools."""

from collections.abc import Callable
from typing import Any

from webdown.core.domain.interfaces.background_processor import BackgroundProcessor


class SyncBackgroundProcessor(BackgroundProcessor):
    """Runs tasks synchronously (blocks until complete).

    Used by MCP tools that need to run generation use cases in-process
    without FastAPI's BackgroundTasks.
    """

    def submit(self, task: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Execute the task immediately (blocks until complete)."""
        task(*args, **kwargs)
