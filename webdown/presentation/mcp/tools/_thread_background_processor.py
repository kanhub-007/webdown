"""Thread-based background processor for MCP tools that need non-blocking execution."""

import threading


class ThreadBackgroundProcessor:
    """Runs tasks in a daemon thread (does not block the caller).

    Used by MCP tools for long-running operations like convert_all_pages
    where the caller should get an immediate job_id and poll for progress.
    """

    def submit(self, task: object, *args: object, **kwargs: object) -> str:
        """Submit the task to a daemon thread and return immediately."""
        thread = threading.Thread(target=task, args=args, kwargs=kwargs, daemon=True, name="mcp-bg-job")
        thread.start()
        return ""
