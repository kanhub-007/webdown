"""SQLite schema initialization."""

from webdown.infrastructure.repositories.sqlite_connection_factory import SqliteConnectionFactory


class SqliteSchemaInitializer:
    """Initializes SQLite database schemas used by the application."""

    def __init__(self, connection_factory: SqliteConnectionFactory) -> None:
        """Initialize with a SQLite connection factory."""
        self._connection_factory = connection_factory

    def initialize(self) -> None:
        """Initialize all database schemas."""
        self.initialize_markdown_storage()

    def initialize_markdown_storage(self) -> None:
        """Initialize markdown storage and progress tables."""
        with self._connection_factory.get_connection("markdown_storage.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS markdown_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    ip_address TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    generation_time_seconds REAL NOT NULL,
                    status TEXT DEFAULT 'completed',
                    base_url TEXT NOT NULL
                )
                """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sitemap_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    lastmod TEXT,
                    FOREIGN KEY (job_id) REFERENCES markdown_files(job_id)
                )
                """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_progress (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    total_pages INTEGER,
                    processed_pages INTEGER DEFAULT 0,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    error_message TEXT
                )
                """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS page_conversion_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    host TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    markdown TEXT,
                    error TEXT,
                    artifact_path TEXT,
                    UNIQUE(job_id, url),
                    FOREIGN KEY (job_id) REFERENCES markdown_files(job_id)
                )
                """)
            # Backwards-compatible schema evolution: add resilience columns to
            # job_progress for databases created before this feature.
            self._add_column_if_missing(cursor, "job_progress", "failed_pages", "INTEGER DEFAULT 0")
            self._add_column_if_missing(cursor, "job_progress", "total_available", "INTEGER")
            self._add_column_if_missing(cursor, "job_progress", "truncated", "INTEGER")
            # Backwards-compatible: host column for fast host-based filtering.
            self._add_column_if_missing(cursor, "page_conversion_status", "host", "TEXT NOT NULL DEFAULT ''")
            # Performance indexes for hot query patterns.
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pcs_status_host ON page_conversion_status(status, host)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pcs_job_status ON page_conversion_status(job_id, status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mf_created_at ON markdown_files(created_at)")
            conn.commit()

    @staticmethod
    def _add_column_if_missing(cursor, table: str, column: str, definition: str) -> None:
        """Add a column to an existing table if it is not already present."""
        cursor.execute(f"PRAGMA table_info({table})")
        existing = {row[1] for row in cursor.fetchall()}
        if column not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
