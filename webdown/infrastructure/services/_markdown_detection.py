"""Markdown detection helpers extracted from the HTML-to-Markdown converter.

Pure detection / classification functions with no side effects.
Used by the main extraction loop and element processors.
"""

from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag


def detect_alert_type(element: Tag) -> tuple[bool, str, str, str]:
    """Detect if an element is a documentation alert/admonition block.

    Returns:
        (is_alert, alert_key, alert_title, alert_icon)
    """
    alert_types = {
        "note": ("ℹ️ Note", "note"),
        "info": ("ℹ️ Info", "info"),
        "tip": ("💡 Tip", "tip"),
        "hint": ("💡 Hint", "hint"),
        "important": ("⚠️ Important", "important"),
        "warning": ("⚠️ Warning", "warning"),
        "caution": ("⚠️ Caution", "caution"),
        "danger": ("🚫 Danger", "danger"),
        "success": ("✅ Success", "success"),
        "example": ("📝 Example", "example"),
        "question": ("❓ Question", "question"),
        "abstract": ("📄 Abstract", "abstract"),
        "quote": ("💬 Quote", "quote"),
        "bug": ("🐛 Bug", "bug"),
        "failure": ("❌ Failure", "failure"),
        "todo": ("📋 Todo", "todo"),
        "check": ("✅ Check", "check"),
        "done": ("✅ Done", "done"),
        "faq": ("❓ FAQ", "faq"),
    }
    classes = " ".join(element.get("class", [])).lower()
    if not any(word in classes for word in ["admonition", "alert", "callout", "theme-doc-alert"]):
        return False, "", "", ""

    for alert_key, (icon_title, _) in alert_types.items():
        if alert_key in classes:
            return True, alert_key, icon_title.split(" ", 1)[1], icon_title.split(" ", 1)[0]

    title_elem = element.find(class_=lambda x: x and "title" in x.lower() if x else False)
    title_text = title_elem.get_text(strip=True).lower() if title_elem else ""
    for alert_key, (icon_title, _) in alert_types.items():
        if alert_key in title_text:
            return True, alert_key, icon_title.split(" ", 1)[1], icon_title.split(" ", 1)[0]

    return True, "note", "Note", "ℹ️"


def _is_last_updated_element(node: Tag) -> bool:
    """Detect 'Last updated'/'Last modified' footer badges."""
    try:
        if not isinstance(node, Tag):
            return False
        if not hasattr(node, "get_text"):
            return False
        text = (node.get_text(" ", strip=True) or "").lower()
        if not text:
            return False

        def has_phrase(t: str) -> bool:
            return "last updated" in t or "last modified" in t or "updated on" in t

        if has_phrase(text):
            if node.find("time") or text.startswith("last updated") or text.startswith("last modified"):
                return True
        if getattr(node, "name", None) == "time":
            parent_text = (
                node.parent.get_text(" ", strip=True).lower()
                if node.parent and hasattr(node.parent, "get_text")
                else ""
            )
            if has_phrase(parent_text):
                return True
    except Exception:
        return False
    return False


def _is_breadcrumb_nav(node: Tag) -> bool:
    """Detect breadcrumb containers."""
    try:
        if not isinstance(node, Tag):
            return False
        name = getattr(node, "name", "").lower()
        if name not in ("nav", "ul", "ol", "div"):
            return False
        aria = (node.get("aria-label") or "").lower()
        if "breadcrumb" in aria:
            return True
        classes = " ".join(node.get("class", [])).lower() if hasattr(node, "get") else ""
        if any(k in classes for k in ("breadcrumb", "breadcrumbs")):
            return True
        if node.find(["ul", "ol"], class_=lambda x: x and ("breadcrumb" in x.lower() or "breadcrumbs" in x.lower())):
            return True
    except Exception:
        return False
    return False


def _mark_processed(element: Tag, processed: set[int]) -> None:
    """Mark an element and all descendants as processed."""
    processed.add(id(element))
    for desc in element.descendants:
        processed.add(id(desc))


def _has_alert_ancestor(element: Tag) -> bool:
    """Check if any ancestor of the element is an alert block."""
    try:
        for parent in element.parents:
            if detect_alert_type(parent)[0]:
                return True
    except Exception:
        pass
    return False


def _should_skip_element(element: Tag, processed: set[int]) -> bool:
    """Check if an element should be skipped."""
    if id(element) in processed:
        return True
    if element.parent and element.parent.name in ("pre", "code", "table"):
        return True
    if any(id(p) in processed for p in element.parents):
        return True
    return False


def _build_breadcrumb_title(soup: BeautifulSoup, base_url: str) -> str:
    """Build a breadcrumb-style title from the URL."""
    parsed = urlparse(base_url)
    path_parts = [p for p in parsed.path.split("/") if p]
    cleaned = []
    for part in path_parts:
        clean = part.replace("-", " ").replace("_", " ")
        clean = " ".join(w.capitalize() for w in clean.split())
        cleaned.append(clean)
    return " / ".join([parsed.netloc] + cleaned)
