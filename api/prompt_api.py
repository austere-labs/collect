from fastapi import APIRouter, Depends, Request, HTTPException
from repository.database import SQLite3Database
from repository.prompt_service import PromptService

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
    return PromptService(conn)


@prompt_api_router.get("/")
async def welcome() -> dict:
    return {"message": "Welcome to the prompt api service"}


@prompt_api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "prompt_api"}


@prompt_api_router.get("/prompts/{prompt_id}")
async def get_prompt(
    prompt_id: str,
    prompt_service: PromptService = Depends(get_prompt_service)
):
    prompt = prompt_service.get_prompt_by_id(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="prompt not found")
