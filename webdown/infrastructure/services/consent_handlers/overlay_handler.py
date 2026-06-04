"""Consent handler that closes overlay/ad popup elements."""

import logging
from typing import ClassVar

from webdown.infrastructure.services.consent_handlers.base import ConsentHandler

logger = logging.getLogger(__name__)


class OverlayCloseHandler(ConsentHandler):
    """Closes consent overlays and ad popups using close/dismiss selectors."""

    SELECTORS: ClassVar[list[str]] = [
        "button[title='Close']",
        ".ca-banner-dismiss",
        "[class*='consent-close']",
        "[aria-label='Dismiss consent banner']",
        "button[aria-label*='Close']",
        "button[class*='close']",
        "[class*='modal'] button[class*='close']",
        "[class*='overlay'] button[class*='close']",
        "[class*='popup'] button[class*='close']",
        "[class*='ad'] button[class*='close']",
        ".modal-close",
        ".popup-close",
        "[data-dismiss='modal']",
        "[id*='close']",
        "div[class*='overlay'] [class*='close']",
        "div[class*='popup'] [class*='close']",
    ]

    async def handle(self, page: object) -> bool:
        """Try each close selector until one succeeds."""
        for selector in self.SELECTORS:
            try:
                locator = page.locator(selector).first
                if await locator.is_visible(timeout=500):
                    await locator.click(timeout=1000)
                    await page.wait_for_timeout(300)
                    logger.debug("PLAYWRIGHT: Overlay closed via %s", selector)
                    return True
            except Exception:
                continue
        return False
