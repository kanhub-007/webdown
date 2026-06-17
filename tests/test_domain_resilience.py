"""Tests for the bulk-conversion resilience domain model (entities + interfaces).

Black-box: asserts the dataclass shape, defaults, and purity (no framework deps).
"""

from dataclasses import is_dataclass

from webdown.core.domain.entities.markdown_job import MarkdownJob
from webdown.core.domain.entities.page_conversion_status import PageConversionStatus
from webdown.core.domain.interfaces.page_error_repository import PageErrorRepository


def test_page_conversion_status_is_a_pure_dataclass_with_expected_fields() -> None:
    """PageConversionStatus carries url/status plus optional markdown/error/artifact."""
    status = PageConversionStatus(
        url="https://example.com/p/a",
        status="success",
        markdown="# A",
        error=None,
        artifact_path=None,
    )

    assert is_dataclass(status)
    assert status.url == "https://example.com/p/a"
    assert status.status == "success"
    assert status.markdown == "# A"
    assert status.error is None
    assert status.artifact_path is None


def test_page_conversion_status_failed_defaults_markdown_none() -> None:
    """A failed page carries an error and no markdown."""
    status = PageConversionStatus(
        url="https://example.com/p/b",
        status="failed",
        error="IndexError: string index out of range",
    )

    assert status.markdown is None
    assert status.error == "IndexError: string index out of range"


def test_markdown_job_has_backwards_compatible_resilience_fields() -> None:
    """MarkdownJob gains failed_pages (and nullable truncation fields) with defaults."""
    from datetime import datetime, timezone

    job = MarkdownJob(
        job_id="J",
        status="completed_with_errors",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        total_pages=534,
        processed_pages=534,
    )

    # New fields default safely so existing constructors/rows still work.
    assert job.failed_pages == 0
    assert job.total_available is None
    assert job.truncated is None


def test_page_error_repository_is_an_abstract_interface() -> None:
    """PageErrorRepository is an ABC declaring the resilience contract."""
    # Cannot instantiate an abstract class with unimplemented methods.
    import pytest

    with pytest.raises(TypeError):
        PageErrorRepository()  # type: ignore[abstract]

    for method in ("save", "save_many", "get_by_job", "get_successful_markdown", "succeeded_urls"):
        assert hasattr(PageErrorRepository, method), f"missing {method}"
