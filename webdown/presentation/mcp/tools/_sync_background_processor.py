"""Synchronous background processor for MCP tools."""


class SyncBackgroundProcessor:
    """Runs tasks synchronously (blocks until complete).

    Used by MCP tools that need to run generation use cases in-process
    without FastAPI's BackgroundTasks.
    """

    def submit(self, task: object, *args: object, **kwargs: object) -> str:
        """Execute the task immediately and return an empty tracking ID."""
        task(*args, **kwargs)
        return ""
