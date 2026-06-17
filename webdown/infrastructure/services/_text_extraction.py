"""Shared text extraction utility used by the HTML-to-Markdown converter.

Extracted to avoid circular imports between the main converter module, the
element processors, and the detection helpers.
"""

import re
from urllib.parse import urljoin

from bs4 import NavigableString, Tag


def _resolve_sibling_text(next_sibling: object | None) -> str:
    """Extract the visible text from a BeautifulSoup sibling node.

    Handles the edge case where ``len()`` on a Tag counts children (not text
    length), so calling ``get_text()`` is required to determine emptiness.
    """
    if isinstance(next_sibling, str):
        return str(next_sibling)
    if next_sibling is not None:
        return next_sibling.get_text()
    return ""


def extract_text_with_links(element: Tag | NavigableString, base_url: str) -> str:
    """Extract text from an element, preserving links as markdown [text](url)."""
    if isinstance(element, NavigableString):
        return str(element).strip()
    result: list[str] = []
    for child in element.children:
        if isinstance(child, NavigableString):
            result.append(str(child))
        elif isinstance(child, Tag):
            if child.name == "a":
                href = child.get("href", "")
                text = child.get_text(strip=True)
                if href and text:
                    full_url = urljoin(base_url, href)
                    result.append(f"[{text}]({full_url})")
                elif text:
                    result.append(text)
            elif child.name in ("strong", "b"):
                text = child.get_text(strip=True)
                if text:
                    sibling_text = _resolve_sibling_text(child.next_sibling)
                    if sibling_text:
                        first_char = sibling_text[0]
                        if not first_char.isspace() and first_char not in ".,;:!?)":
                            result.append(" " + "**" + text + "** ")
                        else:
                            result.append("**" + text + "**")
                    else:
                        result.append("**" + text + "**")
            else:
                result.append(child.get_text())
    text = "".join(result)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
