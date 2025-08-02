# Implementation Plan: `compare_disk_to_db` Function

## Overview

This document outlines the implementation plan for the `compare_disk_to_db` function in the `PromptService` class. The function will synchronize prompt templates between disk (`.claude/commands/*.md` and `_docs/plans/`) and the database, with automatic versioning for changes.

## Current State Analysis

### Database Schema
```sql
-- Current prompt table
CREATE TABLE prompt (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    data JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historical versions table
CREATE TABLE prompt_history (
    id TEXT,
    version INTEGER,
    data JSONB NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_summary TEXT,
    PRIMARY KEY (id, version)
);
```

### Existing Functions in PromptService
- `load_cmds_from_disk()`: Loads all `.md` files from `.claude/commands/`
- `load_plans_from_disk()`: Loads all `.md` files from `_docs/plans/`
- `save_prompt_in_db()`: Adds new prompt or updates existing (handles versioning internally)
- `update_prompt_in_db()`: Updates existing prompt and adds to version history
- `get_prompt_by_id()`: Retrieves prompt by ID
- `get_prompt_by_name()`: Retrieves prompt by name
- `check_exists()`: Checks if prompt exists by name

### Current Issues
1. No `compare_disk_to_db()` method exists
2. No `update_prompt_increment_version()` method exists
3. No method to list all prompts from database
4. No integration point for syncing disk to database

## Implementation Specification

### Core Logic Flow

1. **Load Current State**
   - Get all files from disk using `load_cmds_from_disk()` and `load_plans_from_disk()`
   - Get all active prompts from database using new `list_all_prompts()` method

2. **Compare and Categorize**
   - **New files**: Files on disk not in database
   - **Changed files**: Files on disk with different content hash than database version
   - **Unchanged files**: Files on disk matching database content hash

3. **Process Changes**
   - **New files**: Add using `save_prompt_in_db()` (handles version 1 creation)
   - **Changed files**: Update using `save_prompt_in_db()` (handles version increment)
   - **Unchanged files**: Skip processing

4. **Return Summary**
   - Return detailed summary of operations performed

### Proposed Implementation

#### Method 1: `list_all_prompts`

```python
def list_all_prompts(self) -> List[Prompt]:
    """
    Get all prompts from the database (both CMD and PLAN types)
    
    Returns:
        List[Prompt]: List of all prompts in the database
    """
    cursor = self.conn.cursor()
    cursor.execute(
        """
        SELECT
        id,
        name,
        json(data) as data_json,
        version,
        content_hash,
        created_at,
        updated_at
        FROM prompt
        ORDER BY name, version DESC
        """
    )
    
    prompts = []
    for row in cursor.fetchall():
        data_dict = json.loads(row['data_json'])
        prompt_data = PromptData(**data_dict)
        
        prompt = Prompt(
            id=row['id'],
            name=row['name'],
            data=prompt_data,
            version=row['version'],
            content_hash=row['content_hash'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
        prompts.append(prompt)
    
    return prompts
```

#### Method 2: `compare_disk_to_db`

```python
def compare_disk_to_db(self) -> str:
    """
    Compare prompts on disk to prompts in database.
    - If changes on disk: increment version and update in database
    - If new prompts on disk: persist them with version 1
    
    Returns:
        str: Summary of operations performed
    """
    # Load current disk state
    cmd_result = self.load_cmds_from_disk()
    plan_result = self.load_plans_from_disk()
    
    # Combine all prompts from disk
    disk_prompts = []
    disk_prompts.extend(cmd_result.loaded_prompts)
    disk_prompts.extend(plan_result.loaded_prompts)
    
    # Get current database state
    db_prompts = self.list_all_prompts()
    
    # Create lookup by name for latest versions
    db_by_name = {}
    for prompt in db_prompts:
        if prompt.name not in db_by_name or prompt.version > db_by_name[prompt.name].version:
            db_by_name[prompt.name] = prompt
    
    # Track operations
    new_prompts = []
    updated_prompts = []
    unchanged_prompts = []
    errors = []
    
    # Process each prompt from disk
    for disk_prompt in disk_prompts:
        try:
            if disk_prompt.name in db_by_name:
                # Prompt exists in database - check if content changed
                db_prompt = db_by_name[disk_prompt.name]
                
                if disk_prompt.content_hash != db_prompt.content_hash:
                    # Content changed - update prompt (save_prompt_in_db handles versioning)
                    result = self.save_prompt_in_db(disk_prompt)
                    if result.success:
                        updated_prompts.append(f"{disk_prompt.name} (v{db_prompt.version} -> v{result.version})")
                    else:
                        errors.append(f"{disk_prompt.name}: {result.error_message}")
                else:
                    # Content unchanged
                    unchanged_prompts.append(disk_prompt.name)
            else:
                # New prompt - add to database
                result = self.save_prompt_in_db(disk_prompt)
                if result.success:
                    new_prompts.append(f"{disk_prompt.name} (v1)")
                else:
                    errors.append(f"{disk_prompt.name}: {result.error_message}")
                    
        except Exception as e:
            errors.append(f"{disk_prompt.name}: {str(e)}")
    
    # Generate summary
    summary_parts = []
    if new_prompts:
        summary_parts.append(f"Added {len(new_prompts)} new prompts: {', '.join(new_prompts[:5])}")
        if len(new_prompts) > 5:
            summary_parts[-1] += f" and {len(new_prompts) - 5} more"
    
    if updated_prompts:
        summary_parts.append(f"Updated {len(updated_prompts)} prompts: {', '.join(updated_prompts[:5])}")
        if len(updated_prompts) > 5:
            summary_parts[-1] += f" and {len(updated_prompts) - 5} more"
    
    if unchanged_prompts:
        summary_parts.append(f"Unchanged {len(unchanged_prompts)} prompts")
    
    if errors:
        summary_parts.append(f"Errors: {len(errors)}")
    
    if not summary_parts:
        return "No prompt files found on disk"
    
    return "; ".join(summary_parts)
```

#### Method 3: `update_prompt_increment_version` (Optional Helper)

```python
def update_prompt_increment_version(self, prompt: Prompt) -> PromptCreateResult:
    """
    Helper method to explicitly increment prompt version.
    Note: save_prompt_in_db already handles this internally.
    
    Args:
        prompt: The prompt to update with incremented version
        
    Returns:
        PromptCreateResult: Result of the update operation
    """
    # This is a convenience wrapper around save_prompt_in_db
    # which already handles version incrementing
    return self.save_prompt_in_db(prompt, change_summary="Version increment from disk sync")
```

#### Method 4: `sync_prompts_from_disk` (Public Interface)

```python
def sync_prompts_from_disk(self) -> str:
    """
    Public method to synchronize prompts from disk to database.
    
    Returns:
        str: Summary of sync operations
    """
    print("🔄 Starting prompt synchronization from disk to database...")
    summary = self.compare_disk_to_db()
    print(f"✅ Sync complete: {summary}")
    return summary
```

## Test Scenarios

### Test Cases to Implement

1. **New Prompt File**
   - Create new `.md` file in `.claude/commands/python/`
   - Run sync and verify it gets added as version 1
   - Verify prompt data structure is correct

2. **Modified Prompt File**
   - Modify existing prompt file content
   - Run sync and verify new version is created
   - Verify version number is incremented
   - Verify old version exists in prompt_history

3. **Unchanged Prompt File**
   - Keep prompt file content same
   - Run sync and verify no new version is created
   - Verify function reports as unchanged

4. **Multiple Operations**
   - Mix of new, changed, and unchanged files
   - Verify summary contains all operations

5. **Error Scenarios**
   - File read errors (handled by load methods)
   - Database errors
   - Invalid prompt data

### Test Implementation

```python
def test_compare_disk_to_db(prompt_service: PromptService):
    """Test the compare_disk_to_db functionality"""
    
    # Create test prompts on disk (would need test fixtures)
    # Run sync
    summary = prompt_service.sync_prompts_from_disk()
    
    # Verify results
    assert "Added" in summary or "Updated" in summary or "Unchanged" in summary
    
    # Verify database state
    all_prompts = prompt_service.list_all_prompts()
    assert len(all_prompts) > 0

def test_sync_with_changes(prompt_service: PromptService):
    """Test syncing with modified files"""
    
    # First sync to establish baseline
    initial_summary = prompt_service.sync_prompts_from_disk()
    
    # Modify a file on disk (would need test fixtures)
    
    # Second sync should detect changes
    update_summary = prompt_service.sync_prompts_from_disk()
    assert "Updated" in update_summary
```

## Integration Points

### Usage Examples

```python
# Command-line integration
if __name__ == "__main__":
    db = SQLite3Database(db_path="data/collect.db")
    with db.get_connection() as conn:
        service = PromptService(conn)
        summary = service.sync_prompts_from_disk()
        print(summary)

# As part of startup routine
def initialize_prompts():
    with db.get_connection() as conn:
        service = PromptService(conn)
        # Check directories first
        service.cmd_check_dirs()
        service.plans_check_dirs()
        # Sync from disk
        service.sync_prompts_from_disk()
```

## Performance Considerations

1. **Content Hashing**: SHA256 already implemented in `new_prompt_model`
2. **Batch Operations**: Process prompts individually to avoid memory issues
3. **Database Queries**: Use existing optimized methods
4. **Transaction Management**: Leverage existing connection patterns

## Migration Strategy

1. **Backward Compatibility**: No breaking changes to existing API
2. **Database Schema**: No changes required (uses existing schema)
3. **Existing Data**: All existing prompts remain unchanged
4. **Incremental Rollout**: Can be tested with subset of prompts first

## Implementation Checklist

- [ ] Implement `list_all_prompts` method
- [ ] Implement `compare_disk_to_db` method
- [ ] Implement `sync_prompts_from_disk` public method
- [ ] Add comprehensive unit tests
- [ ] Test with real prompt data
- [ ] Verify performance with full prompt set
- [ ] Add command-line interface for manual sync
- [ ] Update documentation
- [ ] Code review and validation

## Notes

- The existing `save_prompt_in_db` method already handles version incrementing when a prompt with the same name exists
- Content hashing is already implemented using SHA256 in the `new_prompt_model` method
- The implementation leverages existing patterns and methods to minimize code duplication
- Error handling follows existing patterns in the codebase