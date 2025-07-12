# Create SQLite Database Tool

This command helps you create a new SQLite database in the data/ directory using the createdb bash script.

## Tool Definition

The createdb script is a bash tool that:
- Creates a new SQLite database file in the `data/` directory
- Automatically adds the `.db` extension
- Sets appropriate file permissions (644)
- Prevents overwriting existing databases

## Usage Instructions

Use the Bash tool to execute the createdb script with the database name from `$ARGUMENTS`.

### Command Format
```bash
createdb <database_name>
```

### Parameters
- `database_name`: Name for the database (without .db extension)

### Example Commands
```bash
# Create a database named "myapp.db"
createdb myapp

# Create a database named "users.db"
createdb users
```

### Best Practices
- **Check existence first**: Verify the database doesn't already exist to avoid errors
- **Use descriptive names**: Choose clear, meaningful database names
- **Follow naming conventions**: Use lowercase with underscores for multi-word names
- **Document purpose**: Consider adding a comment about the database's purpose

### Error Handling
The script will fail if:
- No database name is provided
- The database already exists
- sqlite3 is not installed
- Insufficient permissions in the current directory

## Task: Create New SQLite Database

Based on the database name provided in `$ARGUMENTS[0]`, execute the createdb script to create a new SQLite database in the data/ directory. The script will handle the creation, extension, and permissions automatically.

Execute: `createdb $ARGUMENTS[0]`
