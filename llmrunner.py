import asyncio
from datetime import datetime

from pydantic import BaseModel
from typing import Dict, Union, List, Optional, Any

from config import Config
from secret_manager import SecretManager
from models.anthropic_mpc import AnthropicMCP
from models.gemini_mcp import GeminiMCP
from models.openai_mpc import OpenAIMCP
from models.xai_mcp import XaiMCP


class ModelsToMCP(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    models_to_mcp: Dict[str, Union[GeminiMCP, AnthropicMCP, OpenAIMCP, XaiMCP]]


class ModelResult(BaseModel):
    model: str
    timestamp: str
    success: bool
    actual_model: Optional[str] = None
    duration_seconds: Optional[float] = None
    response: Optional[Any] = None
    error: Optional[str] = None


class LLMRunnerResults(BaseModel):
    successful_results: List[ModelResult]
    failed_results: List[ModelResult]
    total_models: int
    success_count: int
    failure_count: int


async def llmrunner(prompt: str, models_to_mcp: ModelsToMCP) -> LLMRunnerResults:

    async def call_model(model_name: str) -> dict:
        try:
            start_time = datetime.now()
            iso_time = start_time.isoformat()

            mcp_instance = models_to_mcp.models_to_mcp[model_name]
            print(f"sending to --> {model_name} : at -> {iso_time}")
            response = mcp_instance.send_message(prompt, model=model_name)
            end_time = datetime.now()

            result = ModelResult(
                model=model_name,
                actual_model=model_name,
                timestamp=iso_time,
                duration_seconds=(end_time - start_time).total_seconds(),
                response=response,
                success=True,
            )

            return result

        except Exception as e:
            error_result = ModelResult(
                success=False,
                error=str(e),
                model=model_name,
                timestamp=datetime.now().isoformat(),
            )

            return error_result

    print(
        f"starting runner for: {
          len(models_to_mcp.models_to_mcp.keys())} models ->"
    )
    tasks = [call_model(model) for model in models_to_mcp.models_to_mcp.keys()]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful_results = [
        r for r in results if isinstance(r, ModelResult) and r.success
    ]

    failed_results = [
        r for r in results if isinstance(r, ModelResult) and not r.success
    ]

    return LLMRunnerResults(
        successful_results=successful_results,
        failed_results=failed_results,
        total_models=len(models_to_mcp.models_to_mcp),
        success_count=len(successful_results),
        failure_count=len(failed_results),
    )


def code_review_models_to_mcp():
    config = Config()
    secret_mgr = SecretManager(config.project_id)

    anthropic_model = config.anthropic_default_code_review_model
    gemini_model = config.gemini_default_code_review_model
    xai_model = config.xai_default_code_review_model
    openai_model = config.openai_default_code_review_model

    gemini_mcp = GeminiMCP(config, secret_mgr, gemini_model)
    openai_mcp = OpenAIMCP(config, secret_mgr, openai_model)
    xai_mcp = XaiMCP(config, secret_mgr, xai_model)
    anthropic_mcp = AnthropicMCP(config, secret_mgr, anthropic_model)

    model_mcps = {
        gemini_model: gemini_mcp,
        openai_model: openai_mcp,
        xai_model: xai_mcp,
        anthropic_model: anthropic_mcp,
    }

    return ModelsToMCP(models_to_mcp=model_mcps)
