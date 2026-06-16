"""Tests for the SQLite page-error repository (per-page conversion status).

Classical school: real SQLite against a temp DB; no mocks.
"""

from pathlib import Path

from webdown.core.domain.entities.page_conversion_status import PageConversionStatus
from webdown.infrastructure.database.sqlite_schema_initializer import SqliteSchemaInitializer
from webdown.infrastructure.repositories.sqlite_connection_factory import SqliteConnectionFactory
from webdown.infrastructure.repositories.sqlite_page_error_repository import SqlitePageErrorRepository


def _repo(tmp_path: Path) -> SqlitePageErrorRepository:
    """Build an isolated SQLite-backed page-error repository."""
    connection_factory = SqliteConnectionFactory(str(tmp_path))
    SqliteSchemaInitializer(connection_factory).initialize_markdown_storage()
    return SqlitePageErrorRepository(connection_factory)


def test_save_and_get_round_trips_a_successful_page(tmp_path: Path) -> None:
    """A saved success page is read back with its markdown."""
    repo = _repo(tmp_path)

    repo.save(
        "J",
        PageConversionStatus(url="https://x/p/a", status="success", markdown="# A"),
    )

    [page] = repo.get_by_job("J")
    assert page.url == "https://x/p/a"
    assert page.status == "success"
    assert page.markdown == "# A"
    assert page.error is None


def test_save_many_records_every_page_without_truncation(tmp_path: Path) -> None:
    """All 29 failing URLs are persisted — none dropped (regression for the old 3-cap)."""
    repo = _repo(tmp_path)

    statuses = [
        PageConversionStatus(url=f"https://x/p/fail{i}", status="failed", error=f"err{i}")
        for i in range(29)
    ]
    repo.save_many("J", statuses)

    recorded = repo.get_by_job("J")
    assert len(recorded) == 29
    assert {p.url for p in recorded} == {f"https://x/p/fail{i}" for i in range(29)}
    assert all(p.error and len(p.error) > 0 for p in recorded)


def test_save_upserts_on_rerun_without_duplicating(tmp_path: Path) -> None:
    """Re-saving the same (job_id, url) updates the row instead of inserting a copy."""
    repo = _repo(tmp_path)

    repo.save("J", PageConversionStatus(url="https://x/p/a", status="failed", error="boom"))
    repo.save("J", PageConversionStatus(url="https://x/p/a", status="success", markdown="# A"))

    recorded = repo.get_by_job("J")
    assert len(recorded) == 1
    assert recorded[0].status == "success"   # updated, not duplicated
    assert recorded[0].markdown == "# A"


def test_get_successful_markdown_returns_only_successes(tmp_path: Path) -> None:
    """Successful pages' markdown is returned keyed by URL; failures excluded."""
    repo = _repo(tmp_path)
    repo.save_many(
        "J",
        [
            PageConversionStatus(url="https://x/p/a", status="success", markdown="# A"),
            PageConversionStatus(url="https://x/p/b", status="failed", error="boom"),
            PageConversionStatus(url="https://x/p/c", status="success", markdown="# C"),
        ],
    )

    md = repo.get_successful_markdown("J")
    assert md == {"https://x/p/a": "# A", "https://x/p/c": "# C"}


def test_succeeded_urls_returns_urls_for_a_base_url(tmp_path: Path) -> None:
    """Resume reads the set of URLs already succeeded for a base_url."""
    repo = _repo(tmp_path)
    repo.save_many(
        "J",
        [
            PageConversionStatus(url="https://x/p/a", status="success", markdown="# A"),
            PageConversionStatus(url="https://x/p/b", status="failed", error="boom"),
        ],
    )

    assert repo.succeeded_urls("https://x") == {"https://x/p/a"}


def test_succeeded_urls_matches_on_normalized_host(tmp_path: Path) -> None:
    """base_url host normalization (www-stripped) matches stored URLs."""
    repo = _repo(tmp_path)
    repo.save("J", PageConversionStatus(url="https://www.x.com/p/a", status="success", markdown="# A"))

    # Either www or bare host form should match.
    assert "https://www.x.com/p/a" in repo.succeeded_urls("https://x.com")
