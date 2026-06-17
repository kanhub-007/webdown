"""
DocConvert
 - Responsible for converting HTML to Markdown and pre-processing HTML
   (normalize tables, code blocks, alerts, etc.).
Exports:
 - normalize_html(html: str) -> str
 - extract_markdown_from_html(html: str, base_url: str) -> str
"""

import logging
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from webdown.core.domain.interfaces.html_to_markdown_converter import HtmlToMarkdownConverter
from webdown.infrastructure.services._element_processors import (
    _process_alert_element,
    _process_code_block,
    _process_definition_list,
    _process_details_element,
    _process_figure,
    _process_heading_element,
    _process_image,
    _process_list_item,
    _process_paragraph,
    _process_table,
)
from webdown.infrastructure.services._markdown_detection import (
    _build_breadcrumb_title,
    _has_alert_ancestor,
    _is_breadcrumb_nav,
    _is_last_updated_element,
    _mark_processed,
    _should_skip_element,
    detect_alert_type,
)
from webdown.infrastructure.services._text_extraction import extract_text_with_links

logger = logging.getLogger(__name__)
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


def normalize_html_tables_inplace(soup: BeautifulSoup) -> None:
    """Convert all ARIA tables to standard HTML tables (mutates soup in place)."""
    logger.debug("\n" + "=" * 50 + "\nNORMALIZING HTML: Converting ARIA tables to <table>\n" + "=" * 50)
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


def normalize_html_tables(html_content: str) -> str:
    """Convert all ARIA tables to standard HTML tables (string in, string out).

    Kept for backward compatibility. Prefer parsing once and using
    normalize_html_tables_inplace + normalize_code_blocks on the same soup.
    """
    soup = BeautifulSoup(html_content, "lxml")
    normalize_html_tables_inplace(soup)
    return str(soup)


def _normalize_soup(soup: BeautifulSoup) -> BeautifulSoup:
    """Normalize a BeautifulSoup object: convert ARIA tables and mark code blocks."""
    normalize_html_tables_inplace(soup)
    return normalize_code_blocks(soup)


def normalize_html(html_content: str) -> str:
    """Normalize HTML: convert ARIA tables and mark code blocks (string in, string out).

    Kept for backward compatibility. Prefer _normalize_soup for new code paths.
    """
    soup = _normalize_soup(BeautifulSoup(html_content, "lxml"))
    return str(soup)


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------


def extract_markdown_from_soup(soup: BeautifulSoup, base_url: str) -> str:
    """Convert HTML to Markdown, handling headings, tables, code, alerts, etc.

    Accepts a pre-parsed BeautifulSoup object (use extract_markdown_from_html
    for the legacy string-based entry point).
    """
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


def extract_markdown_from_html(html_content: str, base_url: str) -> str:
    """Convert HTML to Markdown, handling headings, tables, code, alerts, etc.

    Convenience wrapper that parses HTML first. For bulk conversions, use
    extract_markdown_from_soup with a pre-parsed soup to avoid re-parsing.
    """
    soup = BeautifulSoup(html_content, "lxml")
    return extract_markdown_from_soup(soup, base_url)


class BeautifulSoupHtmlToMarkdownConverter(HtmlToMarkdownConverter):
    """HTML-to-Markdown converter backed by BeautifulSoup and pandas."""

    def convert(self, html: str, base_url: str) -> str:
        """Convert HTML content to Markdown.

        Parses the HTML once, then applies normalisation and extraction on the
        same soup object — avoiding the previous triple-parse anti-pattern.
        """
        soup = BeautifulSoup(html, "lxml")
        _normalize_soup(soup)
        return extract_markdown_from_soup(soup, base_url)
