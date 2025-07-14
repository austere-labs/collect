"""Custom datetime adapters for SQLite3 to avoid Python 3.12 deprecation warnings.

This module provides custom adapters and converters for datetime objects when
working with SQLite databases in Python 3.12+, replacing the deprecated default
adapters.
"""

import datetime
import sqlite3


def adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 format.
    
    Args:
        val: datetime.datetime object to adapt
        
    Returns:
        str: ISO 8601 formatted datetime string
    """
    return val.replace(tzinfo=None).isoformat()


def adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 date format.
    
    Args:
        val: datetime.date object to adapt
        
    Returns:
        str: ISO 8601 formatted date string
    """
    return val.isoformat()


def convert_datetime_iso(val):
    """Convert ISO 8601 datetime string to datetime.datetime object.
    
    Args:
        val: bytes object containing ISO 8601 datetime string
        
    Returns:
        datetime.datetime: Parsed datetime object
    """
    return datetime.datetime.fromisoformat(val.decode())


def convert_date_iso(val):
    """Convert ISO 8601 date string to datetime.date object.
    
    Args:
        val: bytes object containing ISO 8601 date string
        
    Returns:
        datetime.date: Parsed date object
    """
    return datetime.date.fromisoformat(val.decode())


def convert_timestamp(val):
    """Convert Unix timestamp to datetime.datetime object.
    
    Args:
        val: bytes object containing Unix timestamp
        
    Returns:
        datetime.datetime: Datetime object from timestamp
    """
    return datetime.datetime.fromtimestamp(int(val))


def register_adapters():
    """Register all custom datetime adapters and converters with sqlite3.
    
    This function should be called once at application startup to configure
    SQLite to use our custom datetime handling instead of the deprecated
    default handlers.
    """
    # Register adapters (Python -> SQLite)
    sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
    sqlite3.register_adapter(datetime.date, adapt_date_iso)
    
    # Register converters (SQLite -> Python)
    sqlite3.register_converter("TIMESTAMP", convert_datetime_iso)
    sqlite3.register_converter("DATETIME", convert_datetime_iso)
    sqlite3.register_converter("DATE", convert_date_iso)


# Automatically register adapters when module is imported
register_adapters()