"""Consent handler for Yahoo/Oath consent banners with scroll-to-reveal."""

import logging
from typing import ClassVar

from webdown.infrastructure.services.consent_handlers.base import ConsentHandler

logger = logging.getLogger(__name__)


class YahooScrollConsentHandler(ConsentHandler):
    """Handles Yahoo/Oath consent banners that require scrolling to reveal buttons."""

    CONTAINERS: ClassVar[list[str]] = [
        "[class*='gdpr']",
        "[class*='fineprint']",
        ".modals--gdpr",
        "[data-test-locator*='consent']",
        "[class*='consent-container']",
        "[class*='consent-modal']",
        "[id*='consent-modal']",
        ".consent-wizard",
    ]

    async def handle(self, page: object) -> bool:
        """Scroll Yahoo consent containers to reveal accept buttons."""
        for container_selector in self.CONTAINERS:
            try:
                container = await page.locator(container_selector).first
                if not await container.is_visible(timeout=500):
                    continue

                await container.hover(timeout=1000)
                await page.wait_for_timeout(200)

                try:
                    await container.evaluate("el => el.scrollTo(0, el.scrollHeight)")
                    await page.wait_for_timeout(500)
                    await container.evaluate("el => el.scrollTo(0, 0)")
                    await page.wait_for_timeout(200)
                    await container.evaluate("el => el.scrollTo(0, el.scrollHeight)")
                    await page.wait_for_timeout(500)
                    await container.evaluate("el => el.focus()")
                    await page.wait_for_timeout(300)
                    logger.debug("PLAYWRIGHT: Scrolled consent container %s", container_selector)
                except Exception:
                    pass
                return True
            except Exception:
                continue
        return False
