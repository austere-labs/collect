from enum import StrEnum
from pathlib import Path
import sys
import requests
from requests.exceptions import (
    RequestException,
    Timeout,
    ConnectionError,
    HTTPError
)
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


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


def load_plans_from_disk() -> dict:
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

    return result


class HTTPMethod(StrEnum):
    POST = "POST"
    GET = "GET"


def runner(
    endpoint: str,
    payload: dict,
    http_method: HTTPMethod,
) -> dict:
    base_url = read_env_value("BASE_API_URL") + ":" + read_env_value("PORT")
    url = base_url + endpoint

    try:
        if http_method is HTTPMethod.POST:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=20,
            )
        elif http_method is HTTPMethod.GET:
            response = requests.get(
                url,
                timeout=20,
            )
        else:
            raise ValueError(f"Unsupported HTTP method: {http_method}")

        # Raise an exception for bad status codes
        response.raise_for_status()

        # Return JSON response
        return response.json()

    except Timeout:
        logger.error(f"Request timed out for {url}")
        raise RuntimeError(f"Request to {endpoint} timed out after 20 seconds")

    except ConnectionError as e:
        logger.error(f"Connection failed for {url}: {e}")
        raise RuntimeError(f"Failed to connect to API at {endpoint}")

    except HTTPError as e:
        logger.error(f"HTTP error {response.status_code} for {url}: {e}")
        raise RuntimeError(
            f"API request failed with status {
                response.status_code}: {response.text}"
        )

    except ValueError as e:
        # Catches JSON decode errors and unsupported method errors
        logger.error(f"Value error for {url}: {e}")
        raise

    except RequestException as e:
        # Catch-all for other requests exceptions
        logger.error(f"Request failed for {url}: {e}")
        raise RuntimeError(f"API request to {endpoint} failed: {str(e)}")

    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error for {url}: {e}")
        raise RuntimeError(f"Unexpected error calling {endpoint}: {str(e)}")


def check_and_register_project(plans: dict) -> bool:
    """
    Check if project exists, register if not.

    Args:
        plans: Dictionary containing github_url and project_name

    Returns:
        bool: True if project exists or was successfully registered
    """
    endpoint = "/projects/" + plans["github_url"]

    try:
        # Try to get the project
        runner(endpoint, {}, HTTPMethod.GET)
        print(f"✅ Project already exists: {plans['github_url']}")
        return True

    except RuntimeError as e:
        # Check if it's a 404 error (project not found)
        if "404" in str(e) or "not found" in str(e).lower():
            print(f"📝 Project not found, registering: {plans['github_url']}")

            # Create project object for registration
            project_data = {
                "github_url": plans["github_url"],
                "description": f"Project: {plans['project_name']}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

            try:
                # Register the project
                register_endpoint = "/register/project"
                result = runner(register_endpoint,
                                project_data, HTTPMethod.POST)
                print(f"✅ Successfully registered project: {result}")
                return True

            except Exception as register_error:
                print(f"❌ Failed to register project: {register_error}")
                return False
        else:
            # Some other error occurred
            print(f"❌ Error checking project: {e}")
            return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    print("Loading plans from disk...")

    # check to see if the project is registered
    # if so then load plans from disk and push
    # else register project and then load plans and push

    plans_json = load_plans_from_disk()
    plan_count = len(plans_json["plans"])
    error_count = len(plans_json["errors"])

    print(f"Found: {plan_count} plans")

    # Check for loading errors first
    if error_count > 0:
        print(f"\n❌ Found {error_count} file loading errors:")
        for error in plans_json["errors"]:
            print(f"  - {error['filename']}: {error['error']}")
        print("\n⚠️  Aborting: Please fix errors before pushing to API")
        return 1

    if plan_count == 0:
        print("No plans found to push to API...")
        return 0

    # Check and register project if needed
    if not check_and_register_project(plans_json):
        print("❌ Failed to ensure project is registered")
        return 1

    print(f"Pushing {plan_count} plans to API >>>")

    result = runner("/load/plans/", plans_json, HTTPMethod.POST)

    # Display results
    if result["success"]:
        print(f"Successfully saved all {len(result['results'])} plans")
        return 0
    else:
        print(f"⚠️ Saved with {result['failed_count']} failures")
        for error in result["errors"]:
            print(f"  ❌ {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
