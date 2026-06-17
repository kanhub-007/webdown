"""Domain service interface for background processing."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class BackgroundProcessor(ABC):
    """Submits work to a background processor."""

    @abstractmethod
    def submit(self, task: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Submit a background task for execution (may be sync or async)."""
