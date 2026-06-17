"""Markdown element-type processors extracted from the HTML-to-Markdown converter.

Each function handles one HTML element type: alerts, headings, code blocks,
details, definition lists, figures, images, tables, paragraphs, and list items.
"""

import logging
import re
from io import StringIO
from urllib.parse import urljoin

import pandas as pd
from bs4 import Tag

from webdown.infrastructure.services._markdown_detection import detect_alert_type
from webdown.infrastructure.services._text_extraction import extract_text_with_links

logger = logging.getLogger(__name__)


def _process_alert_element(element: Tag, output_lines: list[str], base_url: str) -> None:
    """Process an alert/admonition block and append to output_lines."""
    _, alert_type, alert_title, alert_icon = detect_alert_type(element)
    output_lines.append("")
    output_lines.append(f"> {alert_icon} **{alert_title}**")
    output_lines.append(">")

    content_elem = element.find(class_=lambda x: x and "content" in x.lower() if x else False)
    if content_elem:
        for child in content_elem.find_all(["p", "ul", "ol"], recursive=False):
            if child.name == "p":
                text = extract_text_with_links(child, base_url)
                if text:
                    output_lines.append(f"> {text}")
            elif child.name in ("ul", "ol"):
                for li in child.find_all("li", recursive=False):
                    text = extract_text_with_links(li, base_url)
                    if text:
                        output_lines.append(f"> - {text}")
    else:
        text = element.get_text(strip=True)
        for line in text.split("\n"):
            if line.strip():
                output_lines.append(f"> {line.strip()}")

    output_lines.append("")
    logger.debug("  ✓ Alert block: %s - %s", alert_type, alert_title)


def _process_heading_element(
    element: Tag, output_lines: list[str], base_url: str, state: dict
) -> None:
    """Process a heading element with breadcrumb awareness."""
    level = int(element.name[1])
    text = extract_text_with_links(element, base_url)
    if not text:
        return
    if level == 1 and not state["first_h1_encountered"] and state["last_breadcrumb_part"]:
        state["first_h1_encountered"] = True
        if text.lower().strip() == state["last_breadcrumb_part"].strip():
            state["first_h1_matches_breadcrumb"] = True
            logger.debug("  ✓ Skipping H1 (matches breadcrumb): %s", text[:50])
            return
        state["first_h1_matches_breadcrumb"] = False

    if state["first_h1_matches_breadcrumb"] is True:
        adjusted = level
    elif state["first_h1_matches_breadcrumb"] is False:
        adjusted = min(level + 1, 6)
    else:
        adjusted = level

    output_lines.append("")
    output_lines.append("#" * adjusted + " " + text)
    output_lines.append("")


def _process_code_block(element: Tag, output_lines: list[str]) -> None:
    """Process a code block element."""
    language = element.get("data-language", "")
    code_tag = element.find("code")
    code_text = code_tag.get_text() if code_tag else element.get_text()
    code_text = re.sub(r"\$Copy[^$]*\$", "", code_text).strip()
    output_lines.append("")
    output_lines.append(f"```{language}")
    output_lines.append(code_text)
    output_lines.append("```")
    output_lines.append("")


def _process_details_element(element: Tag, output_lines: list[str], base_url: str) -> None:
    """Process a collapsible <details> element."""
    summary = element.find("summary")
    title = extract_text_with_links(summary, base_url) if summary else "Details"
    output_lines.append("")
    output_lines.append(f"> 🔽 **{title}**")
    for child in element.find_all(recursive=False):
        if child.name == "summary":
            continue
        if child.name == "p":
            text = extract_text_with_links(child, base_url)
            if text:
                output_lines.append(f"> {text}")
        elif child.name in ("ul", "ol"):
            for li in child.find_all("li", recursive=False):
                text = extract_text_with_links(li, base_url)
                if text:
                    output_lines.append(f"> - {text}")
    output_lines.append("")


def _process_definition_list(element: Tag, output_lines: list[str], base_url: str) -> None:
    """Process a <dl> definition list."""
    output_lines.append("")
    for dt in element.find_all("dt", recursive=False):
        term = extract_text_with_links(dt, base_url)
        if term:
            output_lines.append(f"**{term}**")
        for sib in dt.next_siblings:
            if getattr(sib, "name", None) == "dt":
                break
            if getattr(sib, "name", None) == "dd":
                definition = extract_text_with_links(sib, base_url)
                if definition:
                    output_lines.append(f": {definition}")
        output_lines.append("")


def _process_figure(element: Tag, output_lines: list[str], base_url: str) -> None:
    """Process a <figure> element."""
    img = element.find("img")
    caption = element.find("figcaption")
    if img:
        src = img.get("src", "")
        alt = img.get("alt", "Image")
        if src:
            output_lines.append(f"![{alt}]({urljoin(base_url, src)})")
    if caption:
        cap_text = extract_text_with_links(caption, base_url)
        if cap_text:
            output_lines.append(f"*{cap_text}*")
    output_lines.append("")


def _process_image(element: Tag, output_lines: list[str], base_url: str) -> None:
    """Process a standalone <img> element (not inside a figure)."""
    if element.find_parent("figure"):
        return
    src = element.get("src", "")
    alt = element.get("alt", "Image")
    if src:
        output_lines.append(f"![{alt}]({urljoin(base_url, src)})")
        output_lines.append("")


def _process_table(element: Tag, output_lines: list[str]) -> None:
    """Process an HTML <table> to Markdown."""
    try:
        df = pd.read_html(StringIO(str(element)))[0]
        if all(isinstance(col, int) for col in df.columns):
            df.columns = df.iloc[0]
            df = df[1:].reset_index(drop=True)
        output_lines.append("")
        output_lines.append(df.to_markdown(index=False))
        output_lines.append("")
    except Exception as exc:
        logger.error("  ✗ Error converting table: %s", exc)


def _process_paragraph(element: Tag, output_lines: list[str], base_url: str) -> None:
    """Process a paragraph, skipping those inside lists or table cells."""
    if any(parent.name in ("li", "td", "th") for parent in element.parents if hasattr(parent, "name")):
        return
    text = extract_text_with_links(element, base_url)
    if text:
        output_lines.append(text)
        output_lines.append("")


def _list_prefix(element: Tag) -> str:
    """Return '1. ' for ordered lists, '- ' for unordered."""
    parent = element.find_parent(["ul", "ol"])
    return "1. " if (parent is not None and parent.name == "ol") else "- "


def _strip_copy_tag(text: str) -> str:
    """Remove '$Copy...$' markers injected by some documentation platforms."""
    return re.sub(r"\$Copy[^$]*\$", "", text).strip()


def _find_json_code_blocks(element: Tag) -> list[tuple[Tag, str]]:
    """Find inline <code> blocks that contain JSON objects."""
    result: list[tuple[Tag, str]] = []
    for code_tag in element.find_all("code", recursive=True):
        if code_tag.find_parent("pre"):
            continue
        code_text = code_tag.get_text().strip()
        match = re.search(r"\{.*\}$", code_text, re.DOTALL) if code_text.startswith("{") else None
        if match:
            result.append((code_tag, match.group(0)))
    return result


def _render_code_blocks_in_li(element: Tag, output_lines: list[str], json_blocks: list[tuple[Tag, str]]) -> None:
    """Append indented Markdown code blocks for <pre> and JSON <code> tags."""
    for pre in element.find_all("pre", attrs={"data-code-block": "true"}):
        lang = pre.get("data-language", "")
        ct = pre.find("code")
        code_text = _strip_copy_tag(ct.get_text() if ct else pre.get_text())
        output_lines.append("")
        output_lines.append(f"   ```{lang}")
        for line in code_text.split("\n"):
            output_lines.append(f"   {line}")
        output_lines.append("   ```")
        output_lines.append("")
    for _tag, json_text in json_blocks:
        json_text = _strip_copy_tag(json_text)
        output_lines.append("")
        output_lines.append("   ```json")
        output_lines.append(f"   {json_text}")
        output_lines.append("   ```")
        output_lines.append("")


def _process_list_item(element: Tag, output_lines: list[str], base_url: str) -> None:
    """Process a list item, handling inline code blocks and JSON."""
    has_code_block = element.find("pre", attrs={"data-code-block": "true"}) is not None
    json_blocks = _find_json_code_blocks(element)
    prefix = _list_prefix(element)

    if has_code_block or json_blocks:
        text_before = _extract_li_text_without_code(element, base_url)
        if text_before:
            output_lines.append(prefix + text_before)
        _render_code_blocks_in_li(element, output_lines, json_blocks)
    else:
        text = extract_text_with_links(element, base_url)
        if text:
            output_lines.append(prefix + text)


def _extract_li_text_without_code(element: Tag, base_url: str) -> str:
    """Extract list-item text after removing code blocks."""
    try:
        from copy import deepcopy

        li_copy = deepcopy(element)
        for pre in li_copy.find_all("pre", attrs={"data-code-block": "true"}):
            pre.decompose()
        for code_tag in li_copy.find_all("code"):
            ct = code_tag.get_text().strip()
            if "{" in ct and ct.endswith("}"):
                match = re.match(r"^(.*?)(\{.*\})$", ct, re.DOTALL)
                if match:
                    prefix = match.group(1).strip()
                    if prefix:
                        new_code = li_copy.new_tag("code")
                        new_code.string = prefix
                        code_tag.replace_with(new_code)
                    else:
                        code_tag.decompose()
        return extract_text_with_links(li_copy, base_url).strip()
    except Exception as exc:
        logger.debug("  Warning: Failed to process list item: %s", exc)
        return extract_text_with_links(element, base_url).strip()
