# Yoyo Database Migrations Cheat Sheet

## Basic Commands

### Creating Migrations
```bash
# Create a new migration with descriptive name
yoyo new ./migrations -m "create_users_table"
yoyo new ./migrations -m "add_email_to_users"
yoyo new ./migrations -m "create_index_on_user_email"

# Create a migration without a message (generates random ID only)
yoyo new ./migrations
```

### Viewing Migration Status
```bash
# List all migrations and their status
yoyo list

# Show detailed migration information
yoyo show-migrations
```

### Applying Migrations
```bash
# Apply all pending migrations
yoyo apply

# Apply migrations up to a specific migration
yoyo apply --migration 20250706_01_sPVrY

# Apply migrations in batch mode (non-interactive)
yoyo apply --batch
```

### Rolling Back Migrations
```bash
# Rollback the last applied migration
yoyo rollback

# Rollback to a specific migration
yoyo rollback --migration 20250706_01_sPVrY

# Rollback all migrations
yoyo rollback --all
```

### Reapplying Migrations
```bash
# Reapply the last migration (rollback then apply)
yoyo reapply

# Reapply a specific migration
yoyo reapply --migration 20250706_01_sPVrY
```

### Development Commands
```bash
# Mark a migration as applied without running it
yoyo mark

# Mark a migration as unapplied without rolling back
yoyo unmark

# Break migration locks (use with caution)
yoyo break-lock
```

## Configuration (yoyo.ini)

```ini
[DEFAULT]
sources = migrations
database = sqlite:///data/prompts.db
batch_mode = on
verbosity = 0
```

### Common Database URLs
```ini
# SQLite
database = sqlite:///path/to/database.db

# PostgreSQL
database = postgresql://user:password@localhost/dbname

# MySQL
database = mysql://user:password@localhost/dbname
```

## Migration File Structure

### Basic Migration Template
```sql
-- Description of what this migration does
-- depends: [optional_parent_migration_id]

-- Your SQL commands here
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Migration with Dependencies
```sql
-- Add email column to users table
-- depends: 20250706_01_sPVrY-create_users_table

ALTER TABLE users ADD COLUMN email TEXT;
```

## Best Practices

1. **Always use descriptive names**: `yoyo new ./migrations -m "create_users_table"`
2. **Use IF NOT EXISTS**: Prevents errors if migration is rerun
3. **Add dependencies**: Use `-- depends:` for migration ordering
4. **Test rollbacks**: Write corresponding DOWN migrations when possible
5. **Keep migrations small**: One logical change per migration
6. **Review before applying**: Use `yoyo list` to check status first

## Common Workflow

```bash
# 1. Create a new migration
yoyo new ./migrations -m "add_user_preferences_table"

# 2. Edit the generated .sql file
# 3. Check migration status
yoyo list

# 4. Apply the migration
yoyo apply

# 5. Verify it was applied
yoyo list
```

## Status Codes

- **U**: Unapplied (pending)
- **A**: Applied (completed)
- **R**: Rollback available

## Troubleshooting

### Common Issues
- **Migration not found**: Check file naming and location
- **Database locked**: Use `yoyo break-lock` (with caution)
- **Dependency issues**: Ensure parent migrations exist and are applied
- **SQL errors**: Check syntax and table/column existence

### Debugging
```bash
# Increase verbosity for more detailed output
yoyo apply --verbosity 2

# Show what would be applied without actually applying
yoyo apply --dry-run
```