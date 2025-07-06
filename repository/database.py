import sqlite3
import json

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from typing import Optional, List, Dict, Any


class Database:
    def __init__(self, db_path: str = "../data/collect.db"):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # enables column access by name
        conn.execute("PRAGMA foreign_keys = ON")  # enables foreign key support
        conn.execute("PRAGMA journal_mode = WAL")  # enables better concurrency
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
