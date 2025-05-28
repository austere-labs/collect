import pytest

from llmrunner import (
    llmrunner,
    code_review_models_to_mcp,
    ModelResult,
    LLMRunnerResults,
)


@pytest.fixture
def models_to_mcp():
    return code_review_models_to_mcp()


@pytest.mark.asyncio
async def test_llmrunner(models_to_mcp):
    prompt = "What is 2 + 2?"
    result = await llmrunner(prompt, models_to_mcp)

    assert isinstance(result, LLMRunnerResults)
    assert isinstance(result.successful_results, list)
    assert isinstance(result.failed_results, list)
    assert isinstance(result.total_models, int)
    assert isinstance(result.success_count, int)
    assert isinstance(result.failure_count, int)

    assert result.total_models == len(models_to_mcp.models_to_mcp)
    assert result.success_count + result.failure_count == result.total_models

    for success_result in result.successful_results:
        assert isinstance(success_result, ModelResult)
        assert success_result.success is True
        assert success_result.model is not None
        assert success_result.timestamp is not None
        assert success_result.response is not None
        assert success_result.duration_seconds is not None

    for failed_result in result.failed_results:
        assert isinstance(failed_result, ModelResult)
        assert failed_result.success is False
        assert failed_result.model is not None
        assert failed_result.timestamp is not None
        assert failed_result.error is not None

    print(f"Total models: {result.total_models}")
    print(f"Successful: {result.success_count}")
    print(f"Failed: {result.failure_count}")

    for failed_result in result.failed_results:
        print(f"Failed model: {
              failed_result.model} - Error: {failed_result.error}")

    for success_result in result.successful_results:
        print(f"Successful model: {success_result.model}")
