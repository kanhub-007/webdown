"""Tests for the BeautifulSoup HTML-to-Markdown converter.

Black-box tests (Classical school): feed real HTML, assert observable Markdown
output. No mocking of BeautifulSoup or internal helpers.
"""

from webdown.infrastructure.services.beautifulsoup_html_to_markdown_converter import (
    BeautifulSoupHtmlToMarkdownConverter,
)


def test_convert_empty_html_returns_empty() -> None:
    """A page with no content returns empty markdown."""
    converter = BeautifulSoupHtmlToMarkdownConverter()

    result = converter.convert("<html><body></body></html>", "https://example.com/")

    assert result == ""


def test_simple_heading_is_converted() -> None:
    """A plain heading produces a markdown heading."""
    converter = BeautifulSoupHtmlToMarkdownConverter()

    result = converter.convert(
        "<html><body><article><h2>The Root</h2><p>Body text.</p></article></body></html>",
        "https://example.com/page",
    )

    assert "## The Root" in result
    assert "Body text." in result


def test_strong_inside_heading_followed_by_empty_decorative_div_does_not_crash() -> None:
    """Regression: Substack headings wrap text in <strong> and append a
    decorative <div class="header-anchor-parent"> whose get_text() is empty.

    Previously this raised ``IndexError: string index out of range`` because the
    guard ``len(next_sibling) > 0`` counts a Tag's *children*, not its text
    length, so it passed even when ``next_sibling.get_text() == ""``.
    """
    converter = BeautifulSoupHtmlToMarkdownConverter()
    html = (
        "<html><body><article>"
        '<h2 class="header-anchor-post">'
        "<strong>AI for Good</strong>"
        '<div class="header-anchor-parent"><div class="anchor-icon"></div></div>'
        "</h2>"
        "<p>Body text.</p>"
        "</article></body></html>"
    )

    # Must not raise.
    result = converter.convert(html, "https://example.com/p/ai-for-good")

    assert "AI for Good" in result
    assert "Body text." in result


def test_strong_as_last_child_of_paragraph_does_not_crash() -> None:
    """Regression: a <strong> with no next sibling (last child) must not crash.

    Previously masked by the earlier IndexError; once that was fixed, processing
    reached paragraphs whose trailing <strong> has ``next_sibling is None``, and
    ``None.get_text()`` raised ``AttributeError``.
    """
    converter = BeautifulSoupHtmlToMarkdownConverter()
    html = (
        "<html><body><article>"
        "<p>Leading text <strong>Trailing Bold</strong></p>"
        "</article></body></html>"
    )

    result = converter.convert(html, "https://example.com/page")

    assert "**Trailing Bold**" in result
    assert "Leading text" in result


def test_strong_followed_by_tag_with_text_emits_bold() -> None:
    """A <strong> followed by a sibling Tag that DOES contain text still works."""
    converter = BeautifulSoupHtmlToMarkdownConverter()
    html = (
        "<html><body><article>"
        "<h2><strong>Important</strong><span> follows</span></h2>"
        "<p>Some body content so the page is not excluded.</p>"
        "</article></body></html>"
    )

    result = converter.convert(html, "https://example.com/page")

    assert "**Important**" in result
    assert "follows" in result


def test_strong_followed_by_punctuation_has_no_trailing_space() -> None:
    """Bold followed by punctuation is not padded with a space before the mark."""
    converter = BeautifulSoupHtmlToMarkdownConverter()
    html = (
        "<html><body><article>"
        "<p><strong>Key</strong> point here.</p>"
        "</article></body></html>"
    )

    result = converter.convert(html, "https://example.com/page")

    assert "**Key** point here" in result
