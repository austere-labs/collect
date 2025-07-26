# Fix Python 3.12 Datetime Adapter Deprecation Warnings

## Status: COMPLETED (2025-01-13)

## Problem

Python 3.12 has deprecated the default datetime adapters and converters in SQLite3, which causes deprecation warnings when using datetime objects with SQLite databases. The warnings appear as:

```
DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
```

## Current State

In `repository/plan_service.py`, we currently:
- Import `datetime` from the datetime module (line 3)
- Use `datetime.now()` to create timestamps (line 71)
- Store datetime objects in the database through Plan objects (lines 115-116, 176, 190-191, 198-199)

## Solution Plan

### 1. Create Custom Datetime Adapters (High Priority)

Create a new module `repository/datetime_adapters.py` with:
- Custom datetime adapter using ISO 8601 format
- Custom datetime converter from ISO 8601 format
- Registration of adapters/converters with sqlite3

### 2. Update Database Schema (Medium Priority)

Ensure the database schema handles datetime storage properly:
- Review current `created_at` and `updated_at` column types
- Update migration if needed to use explicit `TIMESTAMP` type

### 3. Update Plan Service (Medium Priority)

Modify `repository/plan_service.py` to:
- Import the custom datetime adapters
- Use timezone-aware datetime objects where appropriate
- Ensure proper datetime handling in database operations

### 4. Add Tests (Medium Priority)

Create tests to verify:
- Datetime objects are properly stored and retrieved
- No deprecation warnings occur
- Backward compatibility with existing data

### 5. Documentation (Low Priority)

Update documentation to reflect:
- Custom datetime handling approach
- Migration notes for Python 3.12+
- Best practices for datetime usage

## Implementation Details

### Custom Adapter Implementation
```python
import datetime
import sqlite3

def adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 format."""
    return val.replace(tzinfo=None).isoformat()

def convert_datetime_iso(val):
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.datetime.fromisoformat(val.decode())

# Register adapters
sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
sqlite3.register_converter("TIMESTAMP", convert_datetime_iso)
```

### Database Connection Changes
- Use `detect_types=sqlite3.PARSE_DECLTYPES` when creating connections
- Ensure column types are declared as `TIMESTAMP` in schema

## Benefits

1. **Eliminates Deprecation Warnings**: No more warnings in Python 3.12+
2. **Future-Proof**: Uses recommended approach from Python documentation
3. **Consistent Format**: ISO 8601 format is standard and readable
4. **Backward Compatible**: Existing data remains accessible
5. **Timezone Aware**: Can be extended to support timezone-aware datetimes

## Testing Strategy

1. Run existing tests to ensure no regressions
2. Test datetime storage and retrieval
3. Verify no deprecation warnings appear
4. Test with both Python 3.11 and 3.12
5. Test migration from old to new format

## Files Modified

1. ✅ `repository/datetime_adapters.py` (new file) - Created custom adapters
2. ✅ `repository/plan_service.py` - Added import for datetime adapters
3. ✅ `repository/database.py` - Added PARSE_DECLTYPES to connection
4. ❌ `migrations-plans/20250713_03_datetime_adapters.sql` - Not needed, schema already uses TIMESTAMP
5. ✅ `repository/test_datetime_adapters.py` (new file) - Comprehensive test suite
6. ❌ `repository/test_plan_service.py` - No changes needed, tests pass without warnings

## Implementation Summary

- **Phase 1**: ✅ Created custom adapters and updated plan_service.py
- **Phase 2**: ✅ Added comprehensive test suite with 7 tests
- **Phase 3**: ✅ No migration needed, existing schema uses TIMESTAMP
- **Phase 4**: ✅ All tests pass with `-W error::DeprecationWarning`

## Results

- ✅ No more deprecation warnings in Python 3.12+
- ✅ Backward compatible with existing ISO 8601 datetime strings
- ✅ All plan service tests pass without warnings
- ✅ Custom adapters registered automatically on module import
- ✅ Comprehensive test coverage including edge cases

## Notes

- The solution maintains backward compatibility with existing databases
- ISO 8601 format is human-readable and standard
- Can be extended to support timezone-aware datetimes in the future
- Follows Python 3.12 recommendations exactly