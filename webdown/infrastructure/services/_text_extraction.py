"""Shared text extraction utility used by the HTML-to-Markdown converter.

Extracted to avoid circular imports between the main converter module, the
element processors, and the detection helpers.
"""

import re
from urllib.parse import urljoin

from bs4 import NavigableString, Tag


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
                    next_sibling = child.next_sibling
                    # Compute the sibling's text once and check it is non-empty
                    # before indexing. Do NOT use ``len(next_sibling)`` as a guard:
                    # for a BeautifulSoup Tag it counts *children*, not text length
                    # (e.g. Substack headings append a decorative
                    # <div class="header-anchor-parent"> whose children carry no
                    # text, so len > 0 but get_text() == ""). ``next_sibling`` may
                    # also be None when the bold run is the last child.
                    if isinstance(next_sibling, str):
                        sibling_text = str(next_sibling)
                    elif next_sibling is not None:
                        sibling_text = next_sibling.get_text()
                    else:
                        sibling_text = ""
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
