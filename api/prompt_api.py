from fastapi import APIRouter, Depends, Request, HTTPException
from repository.database import SQLite3Database
from repository.prompt_service import PromptService
from config import Config
import json
from api.prompt_api_models import PlanLoader
from repository.prompt_models import PromptType, PromptPlanStatus, PromptCreateResult
import os
import sys
import asyncio
import logging
from textwrap import dedent
from typing import List

logger = logging.getLogger(__name__)

prompt_api_router = APIRouter()


def get_db_connection(request: Request):
    """Create database connection as a dependency using app state"""
    db_path = request.app.state.db_path
    db = SQLite3Database(db_path=db_path)
    conn = db.get_connection()
    try:
        yield conn
    finally:
        conn.close()


def get_prompt_service(conn=Depends(get_db_connection)):
    """Get prompt service instance with injected database connection"""

    config = Config()
    return PromptService(conn, config)


@prompt_api_router.get("/")
async def welcome() -> dict:
    return {"message": "Welcome to the prompt api service"}


@prompt_api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "prompt_api"}


@prompt_api_router.get("/prompts/{prompt_id}")
async def get_prompt(
    prompt_id: str, prompt_service: PromptService = Depends(get_prompt_service)
):
    prompt = prompt_service.get_prompt_by_id(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="prompt not found")

    return prompt


@prompt_api_router.post(
    "/load/plans/",
    summary="Load project plans into database",
    description=dedent(
        """
    Loads project plan files into the database from a JSON payload.

    This endpoint accepts plan data that has been extracted from the filesystem 
    (typically via `tools/loader.py`) and persists it to the database for tracking 
    and management.

    ## Processing Logic

    1. **JSON Parsing:** Validates and parses the input JSON string
    2. **Structure Validation:** Ensures data matches the PlanLoader model schema
    3. **Filename Normalization:** Normalizes filenames to follow conventions
    4. **Plan Creation:** Creates prompt models with type PLAN
    5. **Database Persistence:** Saves each plan, handling duplicates and versioning

    ## Notes

    - Plans are deduplicated based on content hash
    - Automatically handles version incrementing for updated plans
    - Filenames are normalized to use underscores and .md extension
    - Each plan is saved with full audit history
    """
    ).strip(),
    response_model=List[PromptCreateResult],
    response_description=dedent(
        """
    The endpoint returns a list of the processed results of saving the files
    loaded into the database.
    If the file was not successfully saved then the item in the list of results
    will be `success=False`
    and the error message will be available in `error_message`.
    """
    ).strip(),
    responses={
        400: {
            "description": "Invalid JSON or data structure",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid JSON: example error msg"}
                }
            },
        }
    },
)
async def plan_loader(
    plans_json: str, prompt_service: PromptService = Depends(get_prompt_service)
) -> List[PromptCreateResult]:
    """
    Load project plans into the database.

    Args:
        plans_json: JSON string containing project plans with structure:
            {
                "project_name": "collect",
                "github_url": "https://github.com/austere-labs/collect",
                "plans": [
                    {
                        "file_path": "/path/to/plan.md",
                        "filename": "plan_name.md",
                        "status": "drafts|approved|completed",
                        "content": "# Plan content..."
                    }
                ],
                "errors": [
                    {
                        "filename": "/path/to/failed.md",
                        "error": "Error message"
                    }
                ]
            }
        prompt_service: Injected PromptService dependency

    Returns:
        List of PromptCreateResult objects for each processed plan

    Raises:
        HTTPException: 400 error if JSON is invalid or doesn't match schema
    """
    try:
        json_payload = json.loads(plans_json)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    try:
        plan_loader = PlanLoader(**json_payload)
    except Exception as e:  # Changed from json.JSONDecodeError to Exception
        raise HTTPException(status_code=400, detail=f"Invalid data structure: {str(e)}")

    results = []
    for plan in plan_loader.plans:
        filename = plan["filename"]
        if not prompt_service.check_filename(filename):
            filename = prompt_service.normalize_filename(filename)
        prompt = prompt_service.new_prompt_model(
            prompt_content=plan["content"],
            name=filename,
            prompt_type=PromptType.PLAN,
            github_url=plan_loader.github_url,
            status=PromptPlanStatus(plan["status"].upper()),
            project=plan_loader.project_name,
        )
        prompt_create_result = prompt_service.save_prompt_in_db(prompt)
        results.append(prompt_create_result)

    return results


@prompt_api_router.post("/restart")
async def restart_api():
    """
    Restart the API server gracefully.

    This endpoint initiates a server restart by replacing the current process
    with a new one using os.execv(). The response is sent before the restart
    occurs to ensure the client receives confirmation.

    Returns:
        dict: Status message indicating restart has been initiated
    """
    logger.info("API restart requested")

    async def perform_restart():
        """Perform the actual restart after a short delay"""
        await asyncio.sleep(0.5)  # Give time for response to be sent
        logger.info("Executing restart...")

        # Replace the current process with a new one
        # This maintains all environment variables and command-line arguments
        os.execv(sys.executable, [sys.executable] + sys.argv)

    # Schedule the restart as a background task
    asyncio.create_task(perform_restart())

    return {
        "message": "API restart initiated",
        "status": "restarting",
        "note": "Server will be back online shortly",
    }
