"""
DocConvert
 - Responsible for converting HTML to Markdown and pre-processing HTML
   (normalize tables, code blocks, alerts, etc.).
Exports:
 - normalize_html(html: str) -> str
 - extract_markdown_from_html(html: str, base_url: str) -> str
"""

import logging
import re
from io import StringIO
from urllib.parse import urljoin, urlparse

import pandas as pd
from bs4 import BeautifulSoup, NavigableString, Tag

from webdown.core.domain.interfaces.html_to_markdown_converter import HtmlToMarkdownConverter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# ---------------------------------------------------------------------------
# HTML pre-processing
# ---------------------------------------------------------------------------


def convert_aria_table_to_html_table(table_div: Tag, soup: BeautifulSoup) -> Tag | None:
    """Convert a div[role='table'] to a standard HTML <table> element."""
    logger.debug("  Converting ARIA table with classes: %s", table_div.get("class", []))
    all_rows = table_div.find_all("div", role="row", recursive=True)
    logger.debug("  Found %d rows in ARIA table", len(all_rows))
    if not all_rows:
        return None

    new_table = soup.new_tag("table")
    thead = soup.new_tag("thead")
    tbody = soup.new_tag("tbody")
    has_header = False
    headers: list[str] = []

    for row in all_rows:
        header_cells = row.find_all("div", role="columnheader")
        if header_cells:
            tr = soup.new_tag("tr")
            for cell in header_cells:
                th = soup.new_tag("th")
                header_text = cell.get_text(strip=True)
                th.string = header_text
                headers.append(header_text)
                tr.append(th)
            thead.append(tr)
            has_header = True
        else:
            data_cells = row.find_all("div", role="cell")
            if data_cells:
                tr = soup.new_tag("tr")
                for cell in data_cells:
                    td = soup.new_tag("td")
                    td.string = cell.get_text(strip=True)
                    tr.append(td)
                tbody.append(tr)

    if has_header:
        new_table.append(thead)
        logger.debug("  ✓ Added <thead> with headers: %s", headers)
    if tbody.contents:
        new_table.append(tbody)
        logger.debug(
            "  ✓ Created HTML table: %d header rows, %d data rows",
            len(thead.contents) if has_header else 0,
            len(tbody.contents),
        )
        return new_table
    return None


def normalize_code_blocks(soup: BeautifulSoup) -> BeautifulSoup:
    """Mark code blocks with special data attributes for later processing."""
    logger.debug("\nNORMALIZING CODE BLOCKS\n" + "-" * 50)

    pre_tags = soup.find_all("pre")
    logger.debug("Found %d <pre> tags", len(pre_tags))

    code_block_count = 0
    for pre in pre_tags:
        code_tag = pre.find("code")
        language = ""
        if code_tag:
            classes = code_tag.get("class", [])
            for cls in classes:
                if cls.startswith("language-"):
                    language = cls.replace("language-", "")
                    break
                if cls.startswith("lang-"):
                    language = cls.replace("lang-", "")
                    break
        pre["data-code-block"] = "true"
        if language:
            pre["data-language"] = language
        code_block_count += 1
        logger.debug("  Code block %d: language=%s", code_block_count, language or "none")

    inline_count = 0
    for code in soup.find_all("code", recursive=True):
        if code.find_parent("pre"):
            continue
        code["data-inline-code"] = "true"
        inline_count += 1

    logger.debug("Marked %d code blocks and %d inline code elements", code_block_count, inline_count)
    return soup


def normalize_html_tables(html_content: str) -> str:
    """Convert all ARIA tables to standard HTML tables."""
    logger.debug("\n" + "=" * 50 + "\nNORMALIZING HTML: Converting ARIA tables to <table>\n" + "=" * 50)
    soup = BeautifulSoup(html_content, "lxml")
    aria_tables = soup.find_all("div", role="table")
    logger.debug("Found %d ARIA table(s) to convert", len(aria_tables))

    converted_count = 0
    for idx, aria_table in enumerate(aria_tables):
        logger.debug(f"\nConverting ARIA table {idx + 1}/{len(aria_tables)}...")
        html_table = convert_aria_table_to_html_table(aria_table, soup)
        if html_table:
            aria_table.replace_with(html_table)
            converted_count += 1
            logger.debug("  ✓ Replaced ARIA table with HTML <table>")
        else:
            logger.debug("  ✗ Failed to convert, keeping original")

    logger.debug(
        f"\n{'=' * 50}\nCONVERSION COMPLETE: {converted_count}/{len(aria_tables)} tables converted\n{'=' * 50}\n"
    )
    return str(soup)


def normalize_html(html_content: str) -> str:
    """Normalize HTML: convert ARIA tables and mark code blocks."""
    return str(normalize_code_blocks(BeautifulSoup(normalize_html_tables(html_content), "lxml")))


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------


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
                    if next_sibling and hasattr(next_sibling, "__len__") and len(next_sibling) > 0:
                        first_char = (
                            str(next_sibling)[0] if isinstance(next_sibling, str) else next_sibling.get_text()[0]
                        )
                        if first_char and not first_char.isspace() and first_char not in ".,;:!?)":
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


def detect_alert_type(element: Tag) -> tuple[bool, str, str, str]:
    """Detect if an element is a documentation alert/admonition block."""
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


def get_heading_level(element: Tag) -> int | None:
    """Extract heading level from element metadata."""
    el_html = getattr(element, "metadata", None) and getattr(element.metadata, "text_as_html", None)
    if el_html:
        soup = BeautifulSoup(el_html, "lxml")
        for level in range(1, 7):
            if soup.find(f"h{level}"):
                logger.debug("    Found h%d in HTML metadata", level)
                return level
    if getattr(element, "category", None) == "Title":
        if hasattr(element, "metadata") and hasattr(element.metadata, "category_depth"):
            return element.metadata.category_depth
        logger.debug("    Title element, defaulting to h2")
        return 2
    return None


# ---------------------------------------------------------------------------
# Markdown extraction — element-type handlers
# ---------------------------------------------------------------------------


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


def _process_heading_element(element: Tag, output_lines: list[str], base_url: str, state: dict) -> None:
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


def _process_list_item(element: Tag, output_lines: list[str], base_url: str) -> None:
    """Process a list item, handling inline code blocks and JSON."""
    has_code_block = element.find("pre", attrs={"data-code-block": "true"})
    inline_code_tags = element.find_all("code", recursive=True)
    json_code_blocks: list[tuple[Tag, str]] = []
    for code_tag in inline_code_tags:
        if code_tag.find_parent("pre"):
            continue
        code_text = code_tag.get_text().strip()
        if "{" in code_text and code_text.endswith("}"):
            match = re.search(r"\{.*\}$", code_text, re.DOTALL)
            if match:
                json_code_blocks.append((code_tag, match.group(0)))

    parent_list = element.find_parent(["ul", "ol"])
    is_ordered = parent_list is not None and parent_list.name == "ol"

    if has_code_block or json_code_blocks:
        text_before = _extract_li_text_without_code(element, base_url)
        if text_before:
            prefix = "1. " if is_ordered else "- "
            output_lines.append(prefix + text_before)

        for pre in element.find_all("pre", attrs={"data-code-block": "true"}):
            lang = pre.get("data-language", "")
            ct = pre.find("code")
            code_text = ct.get_text() if ct else pre.get_text()
            code_text = re.sub(r"\$Copy[^$]*\$", "", code_text).strip()
            output_lines.append("")
            output_lines.append(f"   ```{lang}")
            for line in code_text.split("\n"):
                output_lines.append(f"   {line}")
            output_lines.append("   ```")
            output_lines.append("")

        for _tag, json_text in json_code_blocks:
            json_text = re.sub(r"\$Copy[^$]*\$", "", json_text).strip()
            output_lines.append("")
            output_lines.append("   ```json")
            output_lines.append(f"   {json_text}")
            output_lines.append("   ```")
            output_lines.append("")
    else:
        text = extract_text_with_links(element, base_url)
        if text:
            prefix = "1. " if is_ordered else "- "
            output_lines.append(prefix + text)


def _extract_li_text_without_code(element: Tag, base_url: str) -> str:
    """Extract list-item text after removing code blocks."""
    try:
        li_soup = BeautifulSoup(str(element), "lxml")
        li_copy = li_soup.find("li")
        if not li_copy:
            return extract_text_with_links(element, base_url).strip()
        for pre in li_copy.find_all("pre", attrs={"data-code-block": "true"}):
            pre.decompose()
        for code_tag in li_copy.find_all("code"):
            ct = code_tag.get_text().strip()
            if "{" in ct and ct.endswith("}"):
                match = re.match(r"^(.*?)(\{.*\})$", ct, re.DOTALL)
                if match:
                    prefix = match.group(1).strip()
                    if prefix:
                        new_code = li_soup.new_tag("code")
                        new_code.string = prefix
                        code_tag.replace_with(new_code)
                    else:
                        code_tag.decompose()
        return extract_text_with_links(li_copy, base_url).strip()
    except Exception as exc:
        logger.debug("  Warning: Failed to process list item: %s", exc)
        return extract_text_with_links(element, base_url).strip()


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


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------


def extract_markdown_from_html(html_content: str, base_url: str) -> str:
    """Convert HTML to Markdown, handling headings, tables, code, alerts, etc."""
    soup = BeautifulSoup(html_content, "lxml")
    output_lines: list[str] = []

    breadcrumb_title = _build_breadcrumb_title(soup, base_url)
    path_parts = [p for p in urlparse(base_url).path.split("/") if p]
    cleaned_parts = [p.replace("-", " ").replace("_", " ") for p in path_parts]

    output_lines.append(f"# {breadcrumb_title}")
    output_lines.append("")

    main_content = soup.find("main") or soup.find("article") or soup.find("body")
    if not main_content:
        main_content = soup

    processed: set[int] = set()
    state: dict = {
        "first_h1_encountered": False,
        "first_h1_matches_breadcrumb": None,
        "last_breadcrumb_part": cleaned_parts[-1].lower() if cleaned_parts else "",
    }

    # Pass 1: direct children (alerts only)
    for element in main_content.find_all(recursive=False):
        if id(element) in processed:
            continue
        if _is_last_updated_element(element) or _is_breadcrumb_nav(element):
            _mark_processed(element, processed)
            continue
        is_alert, _, _, _ = detect_alert_type(element)
        if is_alert:
            _process_alert_element(element, output_lines, base_url)
            _mark_processed(element, processed)

    # Pass 2: all descendants
    for element in main_content.descendants:
        if _should_skip_element(element, processed):
            continue
        if _is_last_updated_element(element) or _is_breadcrumb_nav(element):
            _mark_processed(element, processed)
            continue
        if _has_alert_ancestor(element):
            continue
        if not isinstance(element, Tag):
            continue

        is_alert, _, _, _ = detect_alert_type(element)
        if is_alert:
            _process_alert_element(element, output_lines, base_url)
            _mark_processed(element, processed)
            continue

        tag_name = element.name
        if tag_name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            _process_heading_element(element, output_lines, base_url, state)
            processed.add(id(element))
        elif tag_name == "pre" and element.get("data-code-block") == "true":
            _process_code_block(element, output_lines)
            processed.add(id(element))
        elif tag_name == "details":
            _process_details_element(element, output_lines, base_url)
            _mark_processed(element, processed)
        elif tag_name == "dl":
            _process_definition_list(element, output_lines, base_url)
            _mark_processed(element, processed)
        elif tag_name == "figure":
            _process_figure(element, output_lines, base_url)
            _mark_processed(element, processed)
        elif tag_name == "img":
            _process_image(element, output_lines, base_url)
            processed.add(id(element))
        elif tag_name == "table":
            _process_table(element, output_lines)
            processed.add(id(element))
        elif tag_name == "p":
            _process_paragraph(element, output_lines, base_url)
            processed.add(id(element))
        elif tag_name == "li":
            _process_list_item(element, output_lines, base_url)
            processed.add(id(element))

    # Remove excessive blank lines
    cleaned_lines: list[str] = []
    prev_blank = False
    for line in output_lines:
        is_blank = not line.strip()
        if is_blank and prev_blank:
            continue
        cleaned_lines.append(line)
        prev_blank = is_blank

    content_lines = [line for line in cleaned_lines if line.strip() and not line.strip().startswith("#")]
    if not content_lines:
        logger.warning("\n  Page '%s' has no content beyond headings - EXCLUDING", base_url)
        return ""

    return "\n".join(cleaned_lines).strip()


# ---------------------------------------------------------------------------
# Converter class
# ---------------------------------------------------------------------------


class BeautifulSoupHtmlToMarkdownConverter(HtmlToMarkdownConverter):
    """HTML-to-Markdown converter backed by BeautifulSoup and pandas."""

    def convert(self, html: str, base_url: str) -> str:
        """Convert HTML content to Markdown."""
        normalized_html = normalize_html(html)
        return extract_markdown_from_html(normalized_html, base_url)
