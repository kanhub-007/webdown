"""Streamlit web UI for website scraping and Markdown conversion."""

import concurrent.futures
import logging
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

from webdown.core.application.dto.sitemap_explore_request import SitemapExploreRequest
from webdown.startup.service_factory import (
    create_html_to_markdown_converter,
    create_page_renderer,
    create_sitemap_discovery_service,
)
from webdown.startup.use_case_factory import create_explore_sitemap_use_case

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the Streamlit web application."""
    st.set_page_config(page_title="Website Scraper & Debug", layout="wide")
    st.title("Website Scraper & Markdown Converter")
    st.caption("Open your terminal/console to see debug logs")

    page_renderer = create_page_renderer()
    html_converter = create_html_to_markdown_converter()
    sitemap_service = create_sitemap_discovery_service()

    tab1, tab2, tab3 = st.tabs(["Sitemap Explorer", "Full Site Scraper", "Single Page Scraper"])

    with tab1:
        _render_sitemap_tab()

    with tab2:
        _render_full_site_tab(sitemap_service, page_renderer, html_converter)

    with tab3:
        _render_single_page_tab(page_renderer, html_converter)


def _render_sitemap_tab() -> None:
    """Render the sitemap exploration tab."""
    st.header("Sitemap Explorer")
    base_site_url = st.text_input(
        "Base URL (e.g., https://example.com)", value="https://example.com", key="sitemap_url"
    )
    max_sitemap_pages = st.number_input(
        "Max pages to find",
        min_value=1,
        max_value=100_000,
        value=1000,
        step=100,
        help="Limit the number of pages to discover from sitemaps to prevent long wait times on large websites.",
    )
    if st.button("Find sitemap pages"):
        with st.spinner("Discovering sitemaps and pages..."):
            use_case = create_explore_sitemap_use_case()
            result = use_case.execute(SitemapExploreRequest(base_url=base_site_url, max_pages=max_sitemap_pages))

        st.success(f"Found {len(result.pages)} pages across {len(result.sitemap_files_visited)} sitemap file(s)")
        if result.total_available and result.total_available > len(result.pages):
            st.info(f"Showing {len(result.pages)} of {result.total_available} available (raise the limit to see more).")
        with st.expander("Sitemaps visited", expanded=False):
            for sm in result.sitemap_files_visited:
                st.write(sm)

        if result.pages:
            df_pages = pd.DataFrame([
                {"loc": p.loc, "lastmod": p.lastmod, "changefreq": p.changefreq, "priority": p.priority}
                for p in result.pages
            ])
            for c in ["changefreq", "priority"]:
                if c not in df_pages.columns:
                    df_pages[c] = None
            df_pages = df_pages[["loc", "lastmod", "changefreq", "priority"]]
            st.dataframe(df_pages, use_container_width=True, height=500)

            csv_bytes = df_pages.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv_bytes, file_name="sitemap-pages.csv", mime="text/csv")
        else:
            st.info("No pages discovered. Verify the base URL and that sitemaps are exposed.")


def _render_full_site_tab(sitemap_service: object, page_renderer: object, html_converter: object) -> None:
    """Render the full-site scraping tab."""
    st.header("Full Site to Markdown")
    st.write("Scrape an entire website from its sitemap and combine all content into a single Markdown file.")

    full_site_url = st.text_input("Base URL for Full Scrape", value="https://docs.hyperlane.xyz")
    full_max_pages = st.number_input(
        "Max pages to Scrape",
        min_value=1,
        max_value=10000,
        value=100,
        step=10,
        help="Limit number of pages from sitemap.",
    )

    col1, col2 = st.columns(2)
    with col1:
        whitelist_patterns = st.text_area(
            "Whitelist Patterns (one per line)", help="Only include URLs containing these substrings. Applied first."
        )
    with col2:
        blacklist_patterns = st.text_area(
            "Blacklist Patterns (one per line)",
            help="Exclude URLs containing these substrings. Applied after whitelist.",
        )

    if st.button("Scrape Site & Combine Markdown"):
        with st.spinner(f"Discovering sitemap pages from {full_site_url}..."):
            use_case = create_explore_sitemap_use_case()
            result = use_case.execute(SitemapExploreRequest(base_url=full_site_url, max_pages=full_max_pages))
            pages = [{"loc": p.loc, "lastmod": p.lastmod, "changefreq": p.changefreq, "priority": p.priority}
                     for p in result.pages]
        st.write(f"Found {len(pages)} pages in sitemap (sorted alphabetically).")

        page_urls = [p["loc"] for p in pages]

        whitelist = [p.strip() for p in whitelist_patterns.split("\n") if p.strip()]
        if whitelist:
            page_urls = [url for url in page_urls if any(pat in url for pat in whitelist)]
            st.write(f"After whitelist, {len(page_urls)} pages remain.")

        blacklist = [p.strip() for p in blacklist_patterns.split("\n") if p.strip()]
        if blacklist:
            page_urls = [url for url in page_urls if not any(pat in url for pat in blacklist)]
            st.write(f"After blacklist, {len(page_urls)} pages remain.")

        if not page_urls:
            st.warning("No pages to scrape after filtering.")
        else:
            with st.spinner(f"Rendering {len(page_urls)} pages with Playwright... (this can take a while)"):
                html_results = page_renderer.render_all(page_urls)

            def convert_page(args: tuple[str, str | None]) -> str | None:
                url, html = args
                if html:
                    try:
                        return html_converter.convert(html, url)
                    except Exception as exc:
                        logger.error(f"Error converting {url}: {exc}")
                return None

            all_markdowns: list[str] = []
            progress_bar = st.progress(0, text="Converting HTML to Markdown...")

            inputs = [(url, html_results.get(url)) for url in page_urls]

            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = executor.map(convert_page, inputs)
                for i, result in enumerate(results):
                    if result:
                        all_markdowns.append(result)
                    progress_bar.progress((i + 1) / len(page_urls), text=f"Converted {i + 1}/{len(page_urls)}")

            progress_bar.empty()

            if all_markdowns:
                combined_markdown = "\n\n---\n\n".join(all_markdowns)
                st.success("Scraping and conversion complete!")

                with st.expander("Combined Markdown Preview (first 2000 chars)", expanded=False):
                    st.code(combined_markdown[:2000] + "...")

                domain = urlparse(full_site_url).netloc
                st.download_button(
                    "Download Combined Markdown", combined_markdown, f"{domain}_full_site.md", "text/markdown"
                )


def _render_single_page_tab(page_renderer: object, html_converter: object) -> None:
    """Render the single-page scraper tab."""
    st.header("Single Page Scraper")
    st.write("Render a single URL and convert it to Markdown, with full debug output in the console.")

    single_url = st.text_input(
        "URL to Scrape", value="https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/notation"
    )

    if st.button("Extract Single Page"):
        with st.spinner("1. Rendering with Playwright..."):
            full_html = page_renderer.render(single_url)
            st.success("Playwright rendering complete")

        with st.expander("1. Raw HTML from Playwright (first 2000 chars)", expanded=False):
            st.code((full_html or "")[:2000] + "...")

        with st.spinner("2. Converting to Markdown..."):
            final_markdown = html_converter.convert(full_html or "", single_url)
        st.success("Conversion complete!")

        st.markdown("### Final Extracted Markdown")
        st.markdown(final_markdown)

        domain = urlparse(single_url).netloc or "page"
        path = urlparse(single_url).path.strip("/").replace("/", "_") or "index"

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("Download .md", final_markdown, f"{domain}_{path}.md", "text/markdown")
        with col2:
            st.download_button("Download .txt", final_markdown, f"{domain}_{path}.txt", "text/plain")

        st.info("Open your terminal/console for detailed processing logs.")


if __name__ == "__main__":
    main()
