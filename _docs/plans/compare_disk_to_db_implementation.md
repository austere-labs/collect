# Implementation Plan: `compare_disk_to_db` Function

## Overview

This document outlines the implementation plan for the `compare_disk_to_db` function in the `PromptService` class. The function will synchronize prompt templates between disk (`.claude/commands/*.md`) and the database, with automatic versioning for changes.

## Current State Analysis

### Database Schema
```sql
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_uuid TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    content TEXT NOT NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(prompt_uuid, version)
);
```

### Existing Functions
- `load_claude_commands_from_disk()`: Loads all `.md` files from `.claude/commands/`
- `add_prompt()`: Adds new prompt with version 1
- `list_prompts()`: Gets all active prompts from database
- `get_prompt_by_name()`: Retrieves latest version by name

### Current Issues
1. `compare_disk_to_db()` is a static method with TODO placeholder
2. `update_prompt_increment_version()` is a static method with TODO placeholder
3. Missing `self` parameter in method signatures
4. Line 64 in `persist_load_results()` calls `self.compare_disk_to_db()` but method lacks `self`

## Implementation Specification

### Core Logic Flow

1. **Load Current State**
   - Get all files from disk using `load_claude_commands_from_disk()`
   - Get all active prompts from database using `list_prompts()`

2. **Compare and Categorize**
   - **New files**: Files on disk not in database
   - **Changed files**: Files on disk with different content than latest DB version
   - **Unchanged files**: Files on disk matching latest DB version

3. **Process Changes**
   - **New files**: Add as version 1 using `add_prompt()`
   - **Changed files**: Create new version using `update_prompt_increment_version()`
   - **Unchanged files**: Skip processing

4. **Return Summary**
   - Return string summary of operations performed

### Proposed Implementation

#### Method 1: `compare_disk_to_db`

```python
def compare_disk_to_db(self) -> str:
    """
    Compare prompts on disk to prompts in database.
    - If changes on disk: increment version and update in database
    - If new prompts on disk: persist them with version 1 using add_prompt
    
    Returns:
        str: Summary of operations performed
    """
    import hashlib
    
    # Load current disk state
    load_result = self.load_claude_commands_from_disk()
    if load_result.errors:
        # Log errors but continue processing
        print(f"Errors loading files: {load_result.errors}")
    
    disk_files = load_result.files
    
    # Get current database state (only active prompts)
    db_prompts = self.list_prompts()
    
    # Create lookup by name for latest versions
    db_by_name = {}
    for prompt in db_prompts:
        name = prompt.metadata.get('name')
        if name:
            # Keep only the latest version per name
            if name not in db_by_name or prompt.version > db_by_name[name].version:
                db_by_name[name] = prompt
    
    # Track operations
    new_prompts = []
    updated_prompts = []
    unchanged_prompts = []
    
    # Process each file on disk
    for filename, content in disk_files.items():
        # Create content hash for comparison
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        if filename in db_by_name:
            # File exists in database - check if content changed
            db_prompt = db_by_name[filename]
            db_content_hash = hashlib.md5(db_prompt.content.encode('utf-8')).hexdigest()
            
            if content_hash != db_content_hash:
                # Content changed - create new version
                prompt_data = PromptCreateModel(
                    name=filename,
                    content=content
                )
                new_uuid = self.update_prompt_increment_version(prompt_data, db_prompt.prompt_uuid)
                updated_prompts.append(f"{filename} (v{db_prompt.version} -> v{db_prompt.version + 1})")
            else:
                # Content unchanged
                unchanged_prompts.append(filename)
        else:
            # New file - add as version 1
            prompt_data = PromptCreateModel(
                name=filename,
                content=content
            )
            new_uuid = self.add_prompt(prompt_data)
            new_prompts.append(f"{filename} (v1)")
    
    # Generate summary
    summary_parts = []
    if new_prompts:
        summary_parts.append(f"Added {len(new_prompts)} new prompts: {', '.join(new_prompts)}")
    if updated_prompts:
        summary_parts.append(f"Updated {len(updated_prompts)} prompts: {', '.join(updated_prompts)}")
    if unchanged_prompts:
        summary_parts.append(f"Unchanged {len(unchanged_prompts)} prompts: {', '.join(unchanged_prompts)}")
    
    if not summary_parts:
        return "No prompt files found on disk"
    
    return "; ".join(summary_parts)
```

#### Method 2: `update_prompt_increment_version`

```python
def update_prompt_increment_version(self, prompt_data: PromptCreateModel, existing_uuid: str) -> str:
    """
    Create a new prompt version with the same UUID and incremented version number.
    
    Args:
        prompt_data: The new prompt data to store
        existing_uuid: The UUID of the existing prompt to version
        
    Returns:
        str: The UUID of the updated prompt (same as existing_uuid)
    """
    import json
    
    # Get the current maximum version for this UUID
    with self.db.get_connection(read_only=True) as conn:
        cursor = conn.execute(
            """
            SELECT MAX(version) as max_version
            FROM prompts
            WHERE prompt_uuid = ?
            """,
            (existing_uuid,)
        )
        row = cursor.fetchone()
        max_version = row["max_version"] if row and row["max_version"] else 0
    
    new_version = max_version + 1
    
    # Prepare metadata (preserve existing structure)
    metadata = prompt_data.metadata.copy()
    metadata["name"] = prompt_data.name
    metadata_json = json.dumps(metadata)
    
    # Insert new version
    with self.db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO prompts (prompt_uuid, version, content, metadata)
            VALUES (?, ?, ?, ?)
            """,
            (existing_uuid, new_version, prompt_data.content, metadata_json)
        )
    
    return existing_uuid
```

### Integration Fix

#### Fix in `persist_load_results` method

```python
# Line 64 - Fix missing self parameter
if initial_load is True:
    uuid = self.add_prompt(prompt_data)
    persisted_prompt_uuids.append(uuid)
else:
    summary = self.compare_disk_to_db()  # Add self and capture return value
    print(f"Disk-to-DB sync summary: {summary}")  # Log the summary
```

## Test Scenarios

### Test Cases to Implement

1. **New Prompt File**
   - Add new `.md` file to `.claude/commands/`
   - Verify it gets added as version 1
   - Verify metadata contains correct name

2. **Modified Prompt File**
   - Modify existing prompt file content
   - Verify new version is created with same UUID
   - Verify version number is incremented
   - Verify old version remains in database

3. **Unchanged Prompt File**
   - Keep prompt file content same
   - Verify no new version is created
   - Verify function reports as unchanged

4. **Multiple Operations**
   - Mix of new, changed, and unchanged files
   - Verify summary contains all operations

5. **Error Scenarios**
   - File read errors
   - Database constraint violations
   - Empty content handling

### Mock Test Data Structure

```python
# Test setup
test_files = {
    "new_prompt.md": "# New Prompt\nThis is a new prompt",
    "existing_prompt.md": "# Modified Content\nThis content changed",
    "unchanged_prompt.md": "# Same Content\nThis content stayed same"
}

# Expected database state before test
existing_prompts = [
    PromptResponseModel(
        id=1,
        prompt_uuid="uuid-1",
        version=1,
        content="# Same Content\nThis content stayed same",
        metadata={"name": "unchanged_prompt.md"},
        is_active=True
    ),
    PromptResponseModel(
        id=2,
        prompt_uuid="uuid-2", 
        version=1,
        content="# Original Content\nThis content will change",
        metadata={"name": "existing_prompt.md"},
        is_active=True
    )
]
```

## Dependencies and Imports

### Required Imports
```python
import hashlib  # For content comparison
import json     # Already imported
from typing import List, Optional  # Already imported
```

### External Dependencies
- Uses existing `PromptCreateModel` and `PromptResponseModel`
- Uses existing database connection patterns
- Compatible with current SQLite schema

## Security Considerations

1. **Content Validation**: Validate file content before processing
2. **Path Validation**: Ensure files are within expected directory
3. **SQL Injection**: Use parameterized queries (already implemented)
4. **Error Handling**: Graceful handling of file system and database errors

## Performance Considerations

1. **Content Hashing**: MD5 used for fast content comparison
2. **Database Queries**: Minimize queries by batching operations
3. **Memory Usage**: Process files individually, not all at once
4. **Transaction Management**: Use existing connection patterns

## Migration Strategy

1. **Backward Compatibility**: No breaking changes to existing API
2. **Database Schema**: No schema changes required
3. **Existing Data**: All existing prompts remain unchanged
4. **Rollback Plan**: Function can be disabled by reverting to TODO state

## Future Enhancements

1. **Selective Sync**: Option to sync specific files only
2. **Conflict Resolution**: Handle concurrent modifications
3. **Audit Trail**: Track who made changes and when
4. **Dry Run Mode**: Preview changes before applying
5. **File Deletion Handling**: Handle removed files from disk

## Implementation Checklist

- [ ] Implement `compare_disk_to_db` method
- [ ] Implement `update_prompt_increment_version` method  
- [ ] Fix method signatures (add `self` parameters)
- [ ] Fix integration point in `persist_load_results`
- [ ] Add comprehensive unit tests
- [ ] Test with real data
- [ ] Verify performance with large datasets
- [ ] Update documentation
- [ ] Code review and validation