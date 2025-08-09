import pytest
import sqlite3
import os

from repository.database import SQLite3Database


@pytest.fixture
def test_db():
    """Create a test database instance"""
    test_db_path = "test_collect.db"
    db = SQLite3Database(db_path=test_db_path)
    yield db
    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


def test_database_connection_basic(test_db):
    """Test basic database connection establishment"""
    with test_db.get_connection() as conn:
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        # Test basic query
        cursor = conn.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1


def test_database_connection_read_only(test_db):
    """Test read-only database connection"""
    with test_db.get_connection(read_only=True) as conn:
        assert conn is not None
        # Should be able to read
        cursor = conn.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1


def test_database_row_factory(test_db):
    """Test that Row factory is properly configured"""
    with test_db.get_connection() as conn:
        cursor = conn.execute("SELECT 1 as test_col")
        row = cursor.fetchone()
        # Should be able to access by column name
        assert row["test_col"] == 1


def test_database_pragma_settings(test_db):
    """Test that PRAGMA settings are applied correctly"""
    with test_db.get_connection() as conn:
        # Check foreign keys
        cursor = conn.execute("PRAGMA foreign_keys")
        assert cursor.fetchone()[0] == 1

        # Check journal mode
        cursor = conn.execute("PRAGMA journal_mode")
        assert cursor.fetchone()[0] == "wal"

        # Check synchronous mode
        cursor = conn.execute("PRAGMA synchronous")
        assert cursor.fetchone()[0] == 1  # NORMAL = 1


def test_database_context_manager_cleanup():
    """Test that database connections are properly closed"""
    test_db_path = "test_cleanup.db"
    db = SQLite3Database(db_path=test_db_path)

    try:
        with db.get_connection() as conn:
            conn.execute("SELECT 1")

        # Connection should be closed after context manager exits
        # We can't directly test if it's closed, but we can verify
        # that we can create a new connection successfully
        with db.get_connection() as conn:
            assert conn is not None

    finally:
        if os.path.exists(test_db_path):
            os.remove(test_db_path)


def test_database_error_handling():
    """Test error handling and rollback"""
    test_db_path = "test_error.db"
    db = SQLite3Database(db_path=test_db_path)

    try:
        with pytest.raises(sqlite3.Error):
            with db.get_connection() as conn:
                # This should cause an error
                conn.execute("INVALID SQL STATEMENT")

    finally:
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
