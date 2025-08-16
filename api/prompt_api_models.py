from pydantic import BaseModel
from typing import List


class PlanLoader(BaseModel):
    """Model for plan loader JSON structure"""

    """
      {
      "project_name": "collect",
      "github_url": "https://github.com/austere-labs/collect",
          "plans": [
              {
                  "file_path": "/full/path/to/file.md",
                  "filename": "file.md",
                  "status": "drafts|approved|completed",
                  "content": "file content here"
              }
          ],
          "errors": [
              {
                  "filename": "/path/to/problematic/file.md",
                  "error": "error message"
              }
          ]
      }
    """
    project_name: str
    github_url: str
    plans: List[dict]  # Each dict has: file_path, filename, status, content
    errors: List[dict]  # Each dict has: filename, error
