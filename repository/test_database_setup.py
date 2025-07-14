"""Test database setup utilities for plan service tests."""

import os
import subprocess
from pathlib import Path
import tempfile


def setup_test_database():
    """Set up test database with migrations for plans.
    
    This function:
    1. Removes existing test database if it exists
    2. Runs yoyo migrations to create fresh test database
    3. Raises RuntimeError if migration fails
    
    Returns:
        str: Path to the test database file
    """
    return _setup_database("plans")


def setup_test_prompts_database():
    """Set up test database with migrations for prompts.

    This function:
    1. Removes existing test database if it exists
    2. Runs yoyo migrations to create fresh test database
    3. Raises RuntimeError if migration fails

    Returns:
        str: Path to the test database file
    """
    return _setup_database("prompts")


def _setup_database(db_type: str):
    """Generic function to set up test databases.
    
    Args:
        db_type: Either "plans" or "prompts"
        
    Returns:
        str: Path to the test database file
    """
    # Get project root directory
    project_root = Path(__file__).parent.parent
    
    # Use fixed database names for tests
    if db_type == "plans":
        test_db_path = project_root / "data" / "test_plans.db"
        yoyo_config_template = project_root / "yoyo-test-plans.ini"
    elif db_type == "prompts":
        test_db_path = project_root / "data" / "test_prompts.db"
        yoyo_config_template = project_root / "yoyo-test-prompts.ini"
    else:
        raise ValueError(f"Unknown database type: {db_type}")
    
    # Ensure data directory exists
    test_db_path.parent.mkdir(exist_ok=True)
    
    # Remove existing test database
    if test_db_path.exists():
        os.remove(test_db_path)
    
    # Create temporary yoyo config with database path
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_config:
        # Read template config
        with open(yoyo_config_template, 'r') as template:
            config_content = template.read()
        
        # Replace database path with fixed one
        if db_type == "plans":
            config_content = config_content.replace(
                "sqlite:///data/test_plans.db", 
                f"sqlite:///{test_db_path}"
            )
        else:  # prompts
            config_content = config_content.replace(
                "sqlite:///data/test_prompts.db", 
                f"sqlite:///{test_db_path}"
            )
        
        temp_config.write(config_content)
        temp_config_path = temp_config.name
    
    # Run migrations using yoyo
    try:
        result = subprocess.run([
            "uv", "run", "yoyo", "apply", 
            "--config", temp_config_path, 
            "--batch"
        ], 
        capture_output=True, 
        text=True, 
        cwd=str(project_root),
        check=True
        )
        
        print(f"✅ Test {db_type} database created successfully: {test_db_path}")
        if result.stdout:
            print(f"Migration output: {result.stdout}")
            
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to set up test {db_type} database: {e.stderr}"
        print(f"❌ {error_msg}")
        raise RuntimeError(error_msg)
    finally:
        # Clean up temporary config file
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
    
    return str(test_db_path)


def reset_test_database():
    """Reset test database by removing it and running migrations again.

    This is useful for getting a completely clean state between test runs.

    Returns:
        str: Path to the reset test database file
    """
    print("🔄 Resetting test database...")
    return setup_test_database()


def cleanup_test_database():
    """Clean up test database by removing the file.

    This can be used in test teardown if needed.
    """
    project_root = Path(__file__).parent.parent
    test_db_path = project_root / "data" / "test_plans.db"

    if test_db_path.exists():
        os.remove(test_db_path)
        print(f"🗑️  Test database cleaned up: {test_db_path}")


def get_test_database_path():
    """Get the path to the test database file.

    Returns:
        str: Path to the test database file
    """
    project_root = Path(__file__).parent.parent
    return str(project_root / "data" / "test_plans.db")


if __name__ == "__main__":
    """Command line interface for test database management."""
    import sys

    if len(sys.argv) != 2:
        print("Usage: python test_database_setup.py <setup|reset|cleanup>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "setup":
        setup_test_database()
    elif command == "reset":
        reset_test_database()
    elif command == "cleanup":
        cleanup_test_database()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: setup, reset, cleanup")
        sys.exit(1)
