import sqlite3

from contextlib import contextmanager
from typing import Generator


class SQLite3Database:
    def __init__(self, db_path: str = "../data/collect.db"):
        self.db_path = db_path

    # Decorator that converts this generator function into a context manager
    @contextmanager
    def get_connection(
        self, read_only: bool = False
    ) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections"""
        # Setup phase: runs when entering 'with' block
        # Enable PARSE_DECLTYPES to use our custom datetime converters
        conn = sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.row_factory = sqlite3.Row  # enables column access by name

        # Connection optimizations
        conn.execute("PRAGMA foreign_keys = ON")  # enables foreign key support
        if not read_only:
            # enables better concurrency
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")  # Faster writes
        conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        # Use memory for temp tables
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA mmap_size = 268435456")  # 256MB memory-mapped I/O

        try:
            yield conn  # Pauses here, returns conn to 'with' statement
            # Code inside 'with' block runs here
            if not read_only:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            # Cleanup phase: always runs when exiting 'with' block
            conn.close()
