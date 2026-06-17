"""FastAPI background task adapter."""

from collections.abc import Callable
from typing import Any

from fastapi import BackgroundTasks

from webdown.core.domain.interfaces.background_processor import BackgroundProcessor


class FastApiBackgroundProcessor(BackgroundProcessor):
    """Background processor backed by FastAPI BackgroundTasks."""

    def __init__(self, background_tasks: BackgroundTasks) -> None:
        """Initialize with a FastAPI BackgroundTasks instance."""
        self._background_tasks = background_tasks

    def submit(self, task: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Submit a background task via FastAPI BackgroundTasks."""
        self._background_tasks.add_task(task, *args, **kwargs)
