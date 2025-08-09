"""Test the custom datetime adapters for SQLite3 compatibility."""

import pytest
import warnings
from datetime import datetime, date
from repository.database import SQLite3Database
from repository import datetime_adapters


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    db_path = ":memory:"  # Use in-memory database for tests
    db = SQLite3Database(db_path)

    # Create test table
    with db.get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE test_dates (
                id INTEGER PRIMARY KEY,
                created_at TIMESTAMP,
                updated_at DATETIME,
                date_only DATE,
                description TEXT
            )
        """
        )
        yield conn


def test_datetime_storage_retrieval(test_db):
    """Test that datetime objects can be stored and retrieved without warnings."""

    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Test data
        test_datetime = datetime(2025, 1, 13, 10, 30, 45)
        test_date = date(2025, 1, 13)

        # Insert test data
        test_db.execute(
            """
            INSERT INTO test_dates (created_at, updated_at, date_only, description)
            VALUES (?, ?, ?, ?)
        """,
            (test_datetime, test_datetime, test_date, "Test record"),
        )

        test_db.commit()

        # Retrieve data
        cursor = test_db.execute(
            """
            SELECT created_at, updated_at, date_only, description 
            FROM test_dates WHERE id = 1
        """
        )
        row = cursor.fetchone()

        # Verify no deprecation warnings
        deprecation_warnings = [
            warning for warning in w if issubclass(warning.category, DeprecationWarning)
        ]
        assert (
            len(deprecation_warnings) == 0
        ), f"Found deprecation warnings: {[str(dw.message) for dw in deprecation_warnings]}"

        # Verify data integrity
        assert isinstance(row["created_at"], datetime)
        assert isinstance(row["updated_at"], datetime)
        assert isinstance(row["date_only"], date)
        assert row["created_at"] == test_datetime
        assert row["updated_at"] == test_datetime
        assert row["date_only"] == test_date


def test_datetime_iso_format(test_db):
    """Test that datetimes are stored in ISO format."""

    test_datetime = datetime(2025, 1, 13, 14, 30, 45)

    # Insert using our adapter
    test_db.execute(
        """
        INSERT INTO test_dates (created_at, description)
        VALUES (?, ?)
    """,
        (test_datetime, "ISO format test"),
    )
    test_db.commit()

    # Read raw value (bypass converter)
    cursor = test_db.execute(
        """
        SELECT CAST(created_at AS TEXT) as raw_datetime 
        FROM test_dates WHERE description = 'ISO format test'
    """
    )
    row = cursor.fetchone()

    # Verify ISO format
    expected_iso = "2025-01-13T14:30:45"
    assert row["raw_datetime"] == expected_iso


def test_adapter_functions_directly():
    """Test adapter and converter functions directly."""

    # Test datetime adapter
    test_dt = datetime(2025, 1, 13, 10, 30, 45, 123456)
    adapted = datetime_adapters.adapt_datetime_iso(test_dt)
    assert adapted == "2025-01-13T10:30:45.123456"

    # Test date adapter
    test_date = date(2025, 1, 13)
    adapted_date = datetime_adapters.adapt_date_iso(test_date)
    assert adapted_date == "2025-01-13"

    # Test datetime converter
    iso_bytes = b"2025-01-13T10:30:45.123456"
    converted = datetime_adapters.convert_datetime_iso(iso_bytes)
    assert converted == test_dt

    # Test date converter
    date_bytes = b"2025-01-13"
    converted_date = datetime_adapters.convert_date_iso(date_bytes)
    assert converted_date == test_date

    # Test timestamp converter
    timestamp_bytes = b"1736765445"  # Unix timestamp for 2025-01-13 10:30:45 UTC
    converted_ts = datetime_adapters.convert_timestamp(timestamp_bytes)
    # Note: This will be in local timezone
    assert isinstance(converted_ts, datetime)


def test_timezone_naive_handling():
    """Test that timezone info is properly stripped."""

    # Create timezone-aware datetime
    from datetime import timezone

    tz_aware = datetime(2025, 1, 13, 10, 30, 45, tzinfo=timezone.utc)

    # Adapt should strip timezone
    adapted = datetime_adapters.adapt_datetime_iso(tz_aware)
    assert adapted == "2025-01-13T10:30:45"
    assert "+00:00" not in adapted  # No timezone offset in output


def test_multiple_datetime_operations(test_db):
    """Test multiple datetime operations to ensure no warnings."""

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Multiple inserts
        for i in range(5):
            dt = datetime.now()
            test_db.execute(
                """
                INSERT INTO test_dates (created_at, updated_at, description)
                VALUES (?, ?, ?)
            """,
                (dt, dt, f"Record {i}"),
            )

        test_db.commit()

        # Multiple selects
        cursor = test_db.execute("SELECT * FROM test_dates")
        rows = cursor.fetchall()

        # Verify all datetimes are properly converted
        for row in rows:
            if row["created_at"]:
                assert isinstance(row["created_at"], datetime)
            if row["updated_at"]:
                assert isinstance(row["updated_at"], datetime)

        # Check for warnings
        deprecation_warnings = [
            warning for warning in w if issubclass(warning.category, DeprecationWarning)
        ]
        assert len(deprecation_warnings) == 0


def test_null_datetime_handling(test_db):
    """Test that NULL datetime values are handled correctly."""

    # Insert NULL values
    test_db.execute(
        """
        INSERT INTO test_dates (created_at, updated_at, date_only, description)
        VALUES (NULL, NULL, NULL, 'Null test')
    """
    )
    test_db.commit()

    # Retrieve NULL values
    cursor = test_db.execute(
        """
        SELECT created_at, updated_at, date_only 
        FROM test_dates WHERE description = 'Null test'
    """
    )
    row = cursor.fetchone()

    # Verify NULLs are preserved
    assert row["created_at"] is None
    assert row["updated_at"] is None
    assert row["date_only"] is None


def test_backwards_compatibility(test_db):
    """Test that existing ISO format strings are still readable."""

    # Manually insert ISO format strings (simulating old data)
    test_db.execute(
        """
        INSERT INTO test_dates (id, created_at, updated_at, description)
        VALUES (100, '2024-12-01T10:30:45', '2024-12-01T10:30:45', 'Old format')
    """
    )
    test_db.commit()

    # Read with our converters
    cursor = test_db.execute(
        """
        SELECT created_at, updated_at 
        FROM test_dates WHERE id = 100
    """
    )
    row = cursor.fetchone()

    # Verify conversion works
    assert isinstance(row["created_at"], datetime)
    assert row["created_at"].year == 2024
    assert row["created_at"].month == 12
    assert row["created_at"].day == 1
    assert row["created_at"].hour == 10
    assert row["created_at"].minute == 30
    assert row["created_at"].second == 45
