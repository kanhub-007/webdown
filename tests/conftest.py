"""Shared pytest fixtures for characterization tests."""

import importlib
import importlib.util
import sys
import types
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _install_fake_optional_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Install scoped fake optional modules when they are unavailable.

    The current application imports some third-party integrations at module
    import time. These characterization tests patch those integrations and do
    not exercise real GitHub ingestion or feed parsing. When the optional
    packages are not installed, monkeypatch-scoped fakes keep tests focused on
    API behavior without leaking into later tests.
    """
    if importlib.util.find_spec("gitingest") is None:
        fake_gitingest = types.ModuleType("gitingest")

        def ingest(*_args: object, **_kwargs: object) -> tuple[str, str, str]:
            """Return empty repository ingest data for tests."""
            return "", "", ""

        fake_gitingest.ingest = ingest
        monkeypatch.setitem(sys.modules, "gitingest", fake_gitingest)

    if importlib.util.find_spec("feedparser") is None:
        fake_feedparser = types.ModuleType("feedparser")

        def parse(*_args: object, **_kwargs: object) -> types.SimpleNamespace:
            """Return an empty parsed feed for tests."""
            return types.SimpleNamespace(entries=[])

        fake_feedparser.parse = parse
        monkeypatch.setitem(sys.modules, "feedparser", fake_feedparser)


@pytest.fixture()
def app_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, types.ModuleType]]:
    """Provide a FastAPI test client backed by an isolated temporary database."""
    monkeypatch.setenv("DB_DIR", str(tmp_path))
    _install_fake_optional_modules(monkeypatch)

    for module_name in list(sys.modules):
        if module_name == "webdown" or module_name.startswith("webdown."):
            del sys.modules[module_name]

    main_module = importlib.import_module("webdown.main")

    with TestClient(main_module.app) as client:
        yield client, main_module
