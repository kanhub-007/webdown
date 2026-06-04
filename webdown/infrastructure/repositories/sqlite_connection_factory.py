"""SQLite connection factory."""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class SqliteConnectionFactory:
    """Creates SQLite connections for repository implementations."""

    def __init__(self, db_dir: str | None = None) -> None:
        """Initialize the connection factory.

        Args:
            db_dir: Directory where SQLite database files are stored. When not
                provided, `DB_DIR` is read from the environment and then falls
                back to the repository's `data` directory.
        """
        default_db_dir = Path(__file__).resolve().parents[3] / "data"
        self._db_dir = Path(db_dir or os.getenv("DB_DIR", str(default_db_dir)))
        self._db_dir.mkdir(parents=True, exist_ok=True)

    def database_path(self, database_name: str) -> str:
        """Return the full path for a database file name."""
        return str(self._db_dir / database_name)

    @contextmanager
    def get_connection(self, database_name: str) -> Iterator[sqlite3.Connection]:
        """Open a SQLite connection with row-mapping enabled."""
        conn = sqlite3.connect(self.database_path(database_name), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
