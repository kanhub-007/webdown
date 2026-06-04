"""Base handler for cookie consent chains."""

from abc import ABC, abstractmethod


class ConsentHandler(ABC):
    """Abstract handler in the cookie-consent Chain of Responsibility."""

    def __init__(self) -> None:
        self._next: ConsentHandler | None = None

    def set_next(self, handler: "ConsentHandler") -> "ConsentHandler":
        """Set the next handler in the chain and return it for chaining."""
        self._next = handler
        return handler

    @abstractmethod
    async def handle(self, page: object) -> bool:
        """Attempt to handle consent on the page.

        Returns True when consent was dismissed, False to pass to the next handler.
        """

    async def try_handle(self, page: object) -> bool:
        """Try this handler, then delegate to the next if unsuccessful."""
        if await self.handle(page):
            return True
        if self._next:
            return await self._next.try_handle(page)
        return False
