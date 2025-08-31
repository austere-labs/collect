from fastapi import APIRouter, Depends, Request, HTTPException
from repository.database import SQLite3Database
from repository.prompt_service import PromptService
from config import Config
from api.prompt_api_models import PlanLoader
from repository.prompt_models import PromptType, PromptPlanStatus, Project
import os
import sys
import asyncio
import logging
from typing import Union

logger = logging.getLogger(__name__)

prompt_api_router = APIRouter()

# IMPORTANT: connection creation from fastapi endpoints needs to be async
# That effectively provides a thread per endpoint to sqlite


async def get_db_connection(request: Request):
    """Create database connection as a dependency using app state"""
    db_path = request.app.state.db_path
    db = SQLite3Database(db_path=db_path)
    with db.get_connection() as conn:
        yield conn


async def get_prompt_service(conn=Depends(get_db_connection)):
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


@prompt_api_router.get("/projects/{github_url:path}")
async def get_project(
    github_url: str, prompt_service: PromptService = Depends(get_prompt_service)
) -> Union[Project, dict]:
    """
    Get a project by its GitHub URL.

    Args:
        github_url: The GitHub URL of the project
        prompt_service: Injected PromptService dependency

    Returns:
        Project object if found, or error message dict if not found

    Raises:
        HTTPException: 404 if project not found, 500 on server error
    """
    try:
        project = prompt_service.get_project_by_id(github_url)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"No project found with GitHub URL: {github_url}",
            )
        return project
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve project with url: {github_url}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve project: {str(e)}"
        )


@prompt_api_router.post("/register/project")
async def register_project(
    project: Project, prompt_service: PromptService = Depends(get_prompt_service)
) -> str:
    """
    Register a new project or update an existing one.

    Args:
        project: Project object containing github_url, description, etc.
        prompt_service: Injected PromptService dependency

    Returns:
        str: The github_url of the registered/updated project

    Raises:
        HTTPException: 500 error if registration fails
    """
    try:
        github_url = prompt_service.register_project(project)
        return github_url
    except Exception as e:
        logger.error(f"Failed to register project: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to register project: {str(e)}"
        )


@prompt_api_router.post(
    "/load/plans/",
    summary="Load project plans into database",
)
async def load_plans(
    plan_loader: PlanLoader, prompt_service: PromptService = Depends(get_prompt_service)
) -> dict:
    """
    Load project plans into the database.

    Args:
        plan_loader: PlanLoader object containing plans data
    Returns:
        Dictionary with success status and detailed results

    Raises:
        HTTPException: 400 error if JSON is invalid or doesn't match schema
    """

    results = []
    for plan in plan_loader.plans:
        filename = plan["filename"]
        if not prompt_service.check_filename(filename):
            filename = prompt_service.normalize_filename(filename)

        status_value = plan["status"].lower()

        prompt = prompt_service.new_prompt_model(
            prompt_content=plan["content"],
            name=filename,
            prompt_type=PromptType.PLAN,
            github_url=plan_loader.github_url,
            status=PromptPlanStatus(status_value),
            project=plan_loader.project_name,
        )
        prompt_create_result = prompt_service.save_prompt_in_db(prompt)
        results.append(prompt_create_result)

    # Calculate summary statistics
    failed_plans = [r for r in results if not r.success]
    errors = [r.error_message for r in failed_plans if r.error_message]

    return {
        "success": len(failed_plans) == 0,
        "results": results,
        "total_plans": len(results),
        "successful_plans": len(results) - len(failed_plans),
        "failed_count": len(failed_plans),
        "errors": errors,
    }


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
