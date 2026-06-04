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
            conn.commit()
