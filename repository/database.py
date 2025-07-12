import sqlite3

from contextlib import contextmanager
from typing import Generator


class SQLite3Database:
    def __init__(self, db_path: str = "../data/prompts.db"):
        self.db_path = db_path

    @contextmanager
    def get_connection(
            self,
            read_only: bool = False
    ) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections

        Args:
            read_only: If True, creates a read-only connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # enables column access by name
        # Connection optimizations
        conn.execute("PRAGMA foreign_keys = ON")  # enables foreign key support
        conn.execute("PRAGMA journal_mode = WAL")  # enables better concurrency
        conn.execute("PRAGMA synchronous = NORMAL")  # Faster writes
        conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        # Use memory for temp tables
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA mmap_size = 268435456")  # 256MB memory-mapped I/O

        if read_only:
            conn.execute("PRAGMA query_only = ON")  # For read-only connections

        try:
            yield conn
            if not read_only:
                conn.commit()
        except Exception:
            if not read_only:
                conn.rollback()
            raise
        finally:
            conn.close()
