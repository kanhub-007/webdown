"""Consent handler that clicks accept buttons via selectors."""

import logging
from typing import ClassVar

from webdown.infrastructure.services.consent_handlers.base import ConsentHandler

logger = logging.getLogger(__name__)


class SelectorConsentHandler(ConsentHandler):
    """Clicks consent accept buttons using a prioritized list of selectors."""

    SELECTORS: ClassVar[list[str]] = [
        "button[name='agree'][value='agree']",
        "button[name='agree']",
        ".actions button[name='agree']",
        "form button[name='agree']",
        "button[type='submit'][name='agree']",
        "button[data-test-locator='fineprint-accept-all-button']",
        "button.gdpr-accept-all",
        "#gdpr-accept-all-btn",
        "button[class*='fineprint-approve']",
        "button[class*='ca-banner-accept']",
        ".uh-widget-privacy-consent button.accept-all",
        "button[class*='accept-all']",
        "[class*='consent'] button:has-text('Accept All')",
        "[class*='gdpr'] button:has-text('Accept All Cookies')",
        "button.fc-cta-consent",
        "button.fc-primary-button",
        "button:has-text('Consent')",
        "button:has-text('Accept')",
        "button:has-text('Accept All')",
        "button:has-text('Accept all')",
        "button:has-text('Agree')",
        "button:has-text('I Accept')",
        "button:has-text('I Agree')",
        "button:has-text('OK')",
        "button:has-text('Got it')",
        "button:has-text('Allow all')",
        "button:has-text('Continue')",
        "button:has-text('Alles accepteren')",
        "button:has-text('Accepter alle')",
        "button:has-text('Tout accepter')",
        "button:has-text('Alle akzeptieren')",
        "button:has-text('Aceptar todo')",
        "button:has-text('Accetta tutto')",
        "a:has-text('Accept')",
        "a:has-text('Agree')",
        "[id*='cookie'] button[class*='accept']",
        "[class*='cookie'] button[class*='accept']",
        "[id*='consent'] button[class*='accept']",
        "[class*='consent'] button[class*='accept']",
        "[class*='cookie-banner'] button",
        "[class*='cookie-notice'] button",
        "[id*='cookie-accept']",
        "[class*='cookie-accept']",
        ".cc-btn.cc-dismiss",
        ".cc-allow",
        "#onetrust-accept-btn-handler",
        ".optanon-allow-all",
        "[data-cookiefirst-action='accept']",
        ".didomi-continue-without-agreeing",
        ".qc-cmp2-summary-buttons > button:first-child",
        "button[aria-label*='Accept']",
        "button[aria-label*='Agree']",
        "button[aria-label*='consent']",
        "button[aria-label='Consent']",
        "button[value='agree']",
        "[role='dialog'] button[class*='accept']",
        "[role='dialog'] button[class*='agree']",
    ]

    async def handle(self, page: object) -> bool:
        """Try each consent selector until one succeeds."""
        for selector in self.SELECTORS:
            try:
                locator = page.locator(selector).first
                if await locator.is_visible(timeout=500):
                    await locator.click(timeout=1000)
                    await page.wait_for_timeout(300)
                    logger.debug("PLAYWRIGHT: Consent button clicked via %s", selector)
                    return True
            except Exception as exc:
                logger.debug("PLAYWRIGHT: Consent selector %s failed: %s", selector, exc)
                continue
        return False
