"""Repository and database factory functions."""

from functools import lru_cache

from webdown.infrastructure.database.sqlite_schema_initializer import SqliteSchemaInitializer
from webdown.infrastructure.repositories.sqlite_connection_factory import SqliteConnectionFactory
from webdown.infrastructure.repositories.sqlite_markdown_file_repository import SqliteMarkdownFileRepository
from webdown.infrastructure.repositories.sqlite_markdown_job_repository import SqliteMarkdownJobRepository
from webdown.infrastructure.repositories.sqlite_page_error_repository import SqlitePageErrorRepository


@lru_cache(maxsize=1)
def create_sqlite_connection_factory() -> SqliteConnectionFactory:
    """Create the shared SQLite connection factory."""
    return SqliteConnectionFactory()


@lru_cache(maxsize=1)
def create_schema_initializer() -> SqliteSchemaInitializer:
    """Create the SQLite schema initializer."""
    return SqliteSchemaInitializer(create_sqlite_connection_factory())


@lru_cache(maxsize=1)
def create_markdown_job_repository() -> SqliteMarkdownJobRepository:
    """Create the markdown job repository."""
    return SqliteMarkdownJobRepository(create_sqlite_connection_factory())


@lru_cache(maxsize=1)
def create_markdown_file_repository() -> SqliteMarkdownFileRepository:
    """Create the markdown file repository."""
    return SqliteMarkdownFileRepository(create_sqlite_connection_factory())


@lru_cache(maxsize=1)
def create_page_error_repository() -> SqlitePageErrorRepository:
    """Create the page-error (per-page conversion status) repository."""
    return SqlitePageErrorRepository(create_sqlite_connection_factory())
