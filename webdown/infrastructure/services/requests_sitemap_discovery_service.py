"""
WebSiteExplorer
 - Responsible for discovering sitemap information and site metadata files.
Exports:
 - discover_website_pages(base_url: str, max_pages: int | None = None) -> (list[dict], list[str], int)
 - check_site_metadata_files(base_url: str) -> dict[str, str]
"""

from __future__ import annotations

import gzip
import logging
import re
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from io import BytesIO
from urllib.parse import urlparse, urljoin

import requests
from lxml import etree
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter

from webdown.core.domain.entities.sitemap_url import SitemapUrl
from webdown.core.domain.entities.website_pages import WebsitePages
from webdown.core.domain.interfaces.sitemap_discovery_service import SitemapDiscoveryService

# Configure logging
logger = logging.getLogger(__name__)


# Tunables for concurrency and batching
MAX_WORKERS = 12
BATCH_SIZE = 32

# Precompiled regex for faster robots.txt parsing
_SITEMAP_RE = re.compile(r"^\s*sitemap:\s*(\S+)", re.IGNORECASE)

# Shared HTTP session with connection pooling
_session: requests.Session | None = None


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        adapter = HTTPAdapter(pool_connections=MAX_WORKERS, pool_maxsize=MAX_WORKERS * 4)
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        _session = s
    return _session


def _normalize_base_url(base_url: str) -> str:
    if not base_url:
        raise ValueError("Base URL is empty")
    if not base_url.startswith(("http://", "https://")):
        base_url = "https://" + base_url
    parsed = urlparse(base_url)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc or parsed.path  # handle 'example.com' parsed as path
    if not netloc:
        raise ValueError("Invalid base URL")
    return f"{scheme}://{netloc}"


def _robots_txt_url(base_url: str) -> str:
    root = _normalize_base_url(base_url)
    pu = urlparse(root)
    return f"{pu.scheme}://{pu.netloc}/robots.txt"


def _fetch_bytes(url: str, timeout: int = 15, session: requests.Session | None = None) -> bytes | None:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SitemapExplorer/1.0; +https://example.com/bot)"}
    sess = session or _get_session()
    try:
        resp = sess.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return None
        content = resp.content or b""
        # Detect gzipped content by extension, content-type, or magic number
        is_gz_ext = url.lower().endswith(".gz")
        ct = resp.headers.get("Content-Type", "").lower()
        is_gz_ct = "gzip" in ct or "x-gzip" in ct
        is_gz_magic = content[:2] == b"\x1f\x8b"
        if is_gz_ext or is_gz_ct or is_gz_magic:
            try:
                content = gzip.decompress(content)
            except Exception:
                # Some servers already decompress but keep headers/extensions
                pass
        return content
    except Exception:
        return None


def _looks_like_sitemap(content: bytes) -> bool:
    if not content:
        return False
    # Look into the first chunk only; handle optional namespace prefixes like <sm:urlset> or <ns:sitemapindex>
    head = content[:8192].lower().lstrip()
    # Fast path for common non-namespaced roots
    if b"<urlset" in head or b"<sitemapindex" in head:
        return True
    # Robust detection with optional namespace prefix before the local name
    return bool(re.search(rb"<\s*(?:[a-z0-9_.-]+:)?(?:urlset|sitemapindex)\b", head))


def _find_sitemaps_in_robots(base_url: str) -> list[str]:
    content = _fetch_bytes(_robots_txt_url(base_url), session=_get_session())
    if not content:
        return []
    text = content.decode("utf-8", errors="ignore")
    sitemaps: list[str] = []
    for line in text.splitlines():
        m = _SITEMAP_RE.match(line.strip())
        if m:
            loc = m.group(1).strip()
            # If relative (rare), join with site root
            loc_abs = urljoin(_normalize_base_url(base_url) + "/", loc)
            sitemaps.append(loc_abs)
    return sitemaps


def _candidate_sitemap_urls(base_url: str) -> list[str]:
    root = _normalize_base_url(base_url)
    pu = urlparse(root)
    base = f"{pu.scheme}://{pu.netloc}"
    candidates = [
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/sitemap-index.xml",
        "/sitemap/sitemap.xml",
        "/sitemap1.xml",
        "/sitemap/sitemap-index.xml",
    ]
    return [base + p for p in candidates]


def _discover_sitemap_urls(base_url: str) -> set[str]:
    # Gather candidates, including robots.txt discoveries
    urls = _find_sitemaps_in_robots(base_url) + _candidate_sitemap_urls(base_url)
    # De-duplicate while preserving order
    urls = list(dict.fromkeys(urls))
    discovered: set[str] = set()
    session = _get_session()

    if not urls:
        return discovered

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        fut_map = {ex.submit(_fetch_bytes, url, 15, session): url for url in urls}
        for fut in as_completed(fut_map):
            url = fut_map[fut]
            try:
                content = fut.result()
            except Exception:
                content = None
            if content and _looks_like_sitemap(content):
                discovered.add(url)
    return discovered


def check_site_metadata_files(base_url: str) -> dict[str, str]:
    """
    Checks for common metadata files like robots.txt, RSS/Atom feeds, security.txt, and humans.txt.
    Returns a dictionary of {file_type: found_url}.
    """
    root = _normalize_base_url(base_url)
    session = _get_session()

    candidates = {
        "robots.txt": "/robots.txt",
        "RSS Feed": "/rss.xml",
        "Atom Feed": "/atom.xml",
        "Feed (generic)": "/feed.xml",
        "security.txt": "/.well-known/security.txt",
        "humans.txt": "/humans.txt",
    }

    found_files: dict[str, str] = {}
    for name, path in candidates.items():
        url = urljoin(root, path)
        try:
            content = _fetch_bytes(url, session=session)
            if content:
                found_files[name] = url
        except Exception:
            continue

    return found_files


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _parse_sitemap_streaming(content: bytes, sitemap_url: str) -> tuple[list[str], list[dict]]:
    """Parse a sitemap using streaming lxml (memory-efficient for large files)."""
    child_sitemaps: list[str] = []
    url_entries: list[dict] = []
    try:
        context = etree.iterparse(
            BytesIO(content),
            events=("end",),
            tag=("{*}sitemap", "sitemap", "{*}url", "url"),
            recover=True,
        )
        for _event, elem in context:
            tag = elem.tag
            if isinstance(tag, str) and (tag == "sitemap" or tag.endswith("}sitemap")):
                loc = elem.findtext(".//{*}loc") or elem.findtext("loc")
                if loc:
                    child_sitemaps.append(urljoin(sitemap_url, loc.strip()))
            elif isinstance(tag, str) and (tag == "url" or tag.endswith("}url")):
                loc = elem.findtext(".//{*}loc") or elem.findtext("loc")
                if loc:
                    url_entries.append(
                        _sitemap_entry(
                            loc.strip(),
                            elem.findtext(".//{*}lastmod") or elem.findtext("lastmod"),
                            elem.findtext(".//{*}changefreq") or elem.findtext("changefreq"),
                            elem.findtext(".//{*}priority") or elem.findtext("priority"),
                        )
                    )
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
    except Exception:
        pass
    return child_sitemaps, url_entries


def _parse_sitemap_bs4(content: bytes, sitemap_url: str) -> tuple[list[str], list[dict]]:
    """Parse a sitemap using BeautifulSoup (namespace-tolerant fallback)."""
    child_sitemaps: list[str] = []
    url_entries: list[dict] = []
    try:
        soup = BeautifulSoup(content, "xml")
        for sm in soup.find_all("sitemap"):
            loc_tag = sm.find("loc")
            if loc_tag and loc_tag.text:
                child_sitemaps.append(urljoin(sitemap_url, loc_tag.text.strip()))
        for url_tag in soup.find_all("url"):
            loc_tag = url_tag.find("loc")
            if not loc_tag or not loc_tag.text:
                continue
            url_entries.append(
                _sitemap_entry(
                    loc_tag.text.strip(),
                    url_tag.find("lastmod"),
                    url_tag.find("changefreq"),
                    url_tag.find("priority"),
                )
            )
    except Exception:
        pass
    return child_sitemaps, url_entries


def _sitemap_entry(
    loc: str, lastmod_elem: object | None, changefreq_elem: object | None, priority_elem: object | None
) -> dict:
    """Build a sitemap URL entry dict from parsed elements.

    Each metadata arg may be an element (BeautifulSoup Tag / lxml element, read
    via ``.text``) OR a plain string (lxml ``findtext`` result). The streaming
    parser passes strings; the bs4 fallback passes elements — both must work,
    or the streaming path silently drops lastmod/changefreq/priority.
    """

    def _text(value: object | None) -> str | None:
        if value is None:
            return None
        text = value.text if hasattr(value, "text") else value
        return text.strip() if isinstance(text, str) and text.strip() else None

    return {
        "loc": loc,
        "lastmod": _text(lastmod_elem),
        "changefreq": _text(changefreq_elem),
        "priority": _text(priority_elem),
    }


def _parse_sitemap(content: bytes, sitemap_url: str) -> tuple[list[str], list[dict]]:
    """Parse a sitemap: try streaming lxml first, fall back to BeautifulSoup."""
    child_sitemaps, url_entries = _parse_sitemap_streaming(content, sitemap_url)
    if not child_sitemaps and not url_entries:
        child_sitemaps, url_entries = _parse_sitemap_bs4(content, sitemap_url)
    return child_sitemaps, url_entries


def _same_site(page_url: str, base_url: str) -> bool:
    # Consider same site as equal hostname ignoring leading 'www.'
    def norm_host(u: str) -> str:
        host = urlparse(u).hostname or ""
        return host[4:] if host.startswith("www.") else host

    return norm_host(page_url) == norm_host(_normalize_base_url(base_url))


def _parse_lastmod(lastmod: str | None) -> float | None:
    if not lastmod:
        return None
    s = lastmod.strip()

    # Prefer fromisoformat with 'Z' handled
    s2 = s[:-1] + "+00:00" if s.endswith("Z") else s
    dt = None
    try:
        dt = datetime.fromisoformat(s2)
    except Exception:
        dt = None

    if dt is None:
        # Fallback formats (handle both with and without tz)
        candidates = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
        ]
        s_fallback = s.replace("Z", "+0000") if s.endswith("Z") else s
        for fmt in candidates:
            try:
                dt = datetime.strptime(s_fallback, fmt)
                break
            except Exception:
                continue

    if dt is None:
        return None

    # Ensure timezone-aware UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt.timestamp()


def discover_website_pages(base_url: str, max_pages: int | None = None) -> tuple[list[dict], list[str]]:
    """
    Returns (pages, sitemap_urls_visited)
    pages: list of {'loc': str, 'lastmod': str | None}
    """
    start_sitemaps = _discover_sitemap_urls(base_url)
    visited: set[str] = set()
    queue: deque[str] = deque(start_sitemaps)
    pages: list[dict] = []

    session = _get_session()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        while queue:
            # Discover ALL pages so the caller can report the true total and
            # whether results were truncated. The cap is applied after dedup
            # (see below), not during collection.
            # Take a batch of sitemap URLs to fetch concurrently
            batch: list[str] = []
            while queue and len(batch) < BATCH_SIZE:
                u = queue.popleft()
                if u in visited:
                    continue
                batch.append(u)

            if not batch:
                break

            fut_map = {ex.submit(_fetch_bytes, u, 15, session): u for u in batch}
            for fut in as_completed(fut_map):
                sm_url = fut_map[fut]
                visited.add(sm_url)
                try:
                    content = fut.result()
                except Exception:
                    content = None

                if not content or not _looks_like_sitemap(content):
                    continue

                children, url_entries = _parse_sitemap(content, sm_url)
                pages.extend(url_entries)

                # Enqueue discovered child sitemaps
                for child in children:
                    if child not in visited:
                        queue.append(child)

    deduped = _deduplicate_and_filter(pages, base_url)
    total_available = len(deduped)
    if max_pages and max_pages > 0:
        deduped = deduped[:max_pages]
    return deduped, sorted(list(visited)), total_available


def _deduplicate_and_filter(pages: list[dict], base_url: str) -> list[dict]:
    """Filter same-site, de-duplicate by URL, keep latest lastmod, sort alphabetically."""
    dedup: dict[str, dict] = {}
    for item in pages:
        loc = item.get("loc", "")
        if not loc or not _same_site(loc, base_url):
            continue
        curr = dedup.get(loc)
        if curr is None:
            dedup[loc] = item
        else:
            d1 = _parse_lastmod(curr.get("lastmod"))
            d2 = _parse_lastmod(item.get("lastmod"))
            if d1 is None and d2 is not None:
                dedup[loc] = item
            elif d1 is not None and d2 is not None and d2 > d1:
                dedup[loc] = item

    pages_clean = list(dedup.values())
    pages_clean.sort(key=lambda x: x.get("loc", ""))
    return pages_clean


class RequestsSitemapDiscoveryService(SitemapDiscoveryService):
    """Sitemap discovery service backed by requests and lxml."""

    def discover_website_pages(self, base_url: str, max_pages: int | None = None) -> WebsitePages:
        """Discover website pages from sitemap files."""
        pages, sitemap_files, total_available = discover_website_pages(base_url, max_pages=max_pages)
        truncated = (
            max_pages is not None
            and max_pages > 0
            and total_available is not None
            and total_available > len(pages)
        )
        return WebsitePages(
            pages=[
                SitemapUrl(
                    loc=page.get("loc", ""),
                    lastmod=page.get("lastmod"),
                    changefreq=page.get("changefreq"),
                    priority=page.get("priority"),
                )
                for page in pages
            ],
            sitemap_files_visited=sitemap_files,
            total_available=total_available,
            truncated=truncated,
        )
