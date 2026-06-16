"""Tests for sitemap discovery fidelity: truncation signal + metadata propagation.

Classical school: the REAL RequestsSitemapDiscoveryService against monkeypatched
network helpers (canned XML). Covers specs/2026-06-16_sitemap-fidelity/.

ADR-2 note: the metadata test is a reproduction fixture. The chain was audited
as correct since the initial commit; this test confirms it and guards against
regression. If it ever fails, THAT is the signal to hunt the metadata bug.
"""

import webdown.infrastructure.services.requests_sitemap_discovery_service as discovery_mod
from webdown.infrastructure.services.requests_sitemap_discovery_service import (
    RequestsSitemapDiscoveryService,
)

BASE = "https://x.com"


def _urlset_xml(n: int, *, with_meta: bool = False) -> bytes:
    """Build a sitemap urlset with n pages."""
    rows = []
    for i in range(n):
        loc = f"{BASE}/p/{i}"
        if with_meta:
            rows.append(
                f"<url><loc>{loc}</loc><lastmod>2026-06-{i+1:02d}</lastmod>"
                f"<changefreq>monthly</changefreq><priority>0.{i}</priority></url>"
            )
        else:
            rows.append(f"<url><loc>{loc}</loc></url>")
    body = "".join(rows)
    return (
        '<?xml version="1.0"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{body}</urlset>"
    ).encode("utf-8")


def _patch_network(monkeypatch, xml: bytes):
    """Make discovery hit only one canned sitemap."""
    monkeypatch.setattr(discovery_mod, "_discover_sitemap_urls", lambda base_url: [f"{BASE}/sitemap.xml"])
    monkeypatch.setattr(discovery_mod, "_fetch_bytes", lambda url, timeout=15, session=None: xml)


def test_truncation_signal_when_max_pages_caps_results(monkeypatch) -> None:
    """S1: 5-page site, max_pages=2 -> 2 returned, total_available=5, truncated=True."""
    _patch_network(monkeypatch, _urlset_xml(5))

    result = RequestsSitemapDiscoveryService().discover_website_pages(BASE, max_pages=2)

    assert len(result.pages) == 2
    assert result.total_available == 5
    assert result.truncated is True


def test_no_truncation_when_all_returned(monkeypatch) -> None:
    """max_pages=0 (unlimited) returns everything; truncated=False."""
    _patch_network(monkeypatch, _urlset_xml(5))

    result = RequestsSitemapDiscoveryService().discover_website_pages(BASE, max_pages=0)

    assert len(result.pages) == 5
    assert result.total_available == 5
    assert result.truncated is False


def test_no_truncation_when_cap_exceeds_total(monkeypatch) -> None:
    """max_pages larger than total returns all; truncated=False."""
    _patch_network(monkeypatch, _urlset_xml(3))

    result = RequestsSitemapDiscoveryService().discover_website_pages(BASE, max_pages=1000)

    assert len(result.pages) == 3
    assert result.total_available == 3
    assert result.truncated is False


def test_metadata_is_propagated_from_xml(monkeypatch) -> None:
    """ADR-2 reproduction: lastmod/changefreq/priority are populated (chain is correct)."""
    _patch_network(monkeypatch, _urlset_xml(3, with_meta=True))

    result = RequestsSitemapDiscoveryService().discover_website_pages(BASE, max_pages=0)

    [first] = [p for p in result.pages if p.loc.endswith("/p/0")]
    assert first.lastmod == "2026-06-01"
    assert first.changefreq == "monthly"
    assert first.priority == "0.0"


def test_default_max_pages_is_1000(monkeypatch) -> None:
    """ADR-3: the MCP default is 1000 (covers most sites in one call)."""
    from webdown.core.application.dto.sitemap_explore_request import SitemapExploreRequest

    _patch_network(monkeypatch, _urlset_xml(3))

    # The DTO default drives the explore tool default.
    assert SitemapExploreRequest(base_url=BASE).max_pages == 1000
