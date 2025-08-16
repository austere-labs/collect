from pathlib import Path
import json


def read_env_value(key: str) -> str:
    """Simple .env file reader to get a specific key"""
    project_dir = Path(__file__).parent.parent
    env_file = project_dir / ".env"

    if not env_file.exists():
        return ""

    try:
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                # Parse KEY=VALUE format
                if "=" in line:
                    env_key, env_value = line.split("=", 1)
                    if env_key.strip() == key:
                        return env_value.strip()
    except Exception:
        pass

    return ""


def load_plans_from_disk() -> str:
    """Load all plan files from disk and return as JSON string"""
    project_dir = Path(__file__).parent.parent
    plans_dir = project_dir / "_docs" / "plans"

    # Get GitHub URL from .env file
    github_url = read_env_value("GITHUB_URL")

    # Get project name from directory
    project_name = project_dir.name

    result = {
        "project_name": project_name,
        "github_url": github_url,
        "plans": [],
        "errors": [],
    }

    status_dirs = ["drafts", "approved", "completed"]

    for status in status_dirs:
        subdir = plans_dir / status
        if subdir.exists() and subdir.is_dir():
            for file in subdir.iterdir():
                if file.is_file():
                    try:
                        content = file.read_text()
                        result["plans"].append(
                            {
                                "file_path": str(file),
                                "filename": file.name,
                                "status": status,
                                "content": content,
                            }
                        )
                    except Exception as e:
                        result["errors"].append(
                            {"filename": str(file), "error": str(e)}
                        )

    return json.dumps(result, indent=2)
