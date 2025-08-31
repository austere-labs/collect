from config import Config
from secret_manager import SecretManager
from models.anthropic_prompt_generate import PromptGenerateResponse
from models.anthropic_prompt_improve import PromptImproveResponse
from models.anthropic_prompt_templatize import PromptTemplatizeResponse
from models.anthropic_models import AnthropicRequest, AnthropicResponse
import requests


class AnthropicMCP:
    def __init__(
        self,
        config: Config,
        secret_mgr: SecretManager,
        model: str,
    ) -> None:
        self.config = config
        self.secret_mgr = secret_mgr
        self.model = model
        self.headers = self.build_headers()

    def build_headers(self) -> dict:
        anthropic_key = self.secret_mgr.get_secret(self.config.anthropic_key_path)

        return {
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "prompt-tools-2025-04-02",
        }

    def get_model_list(self):
        response = requests.get(
            "https://api.anthropic.com/v1/models", headers=self.headers
        )
        response.raise_for_status()

        model_data = response.json()
        name_list = [model["id"] for model in model_data["data"]]

        return name_list

    def extract_text(self, ai_response: dict) -> str:
        """Extract text from Anthropic response format."""
        if not isinstance(ai_response, dict):
            return str(ai_response)

        # Anthropic format
        if "content" in ai_response:
            content = ai_response["content"]
            if isinstance(content, list) and content:
                return content[0].get("text", "")

        return str(ai_response)

    def send_message(
        self, message: str, max_tokens: int = 1024, model: str = None
    ) -> dict:
        try:
            # Use provided model or default to config model
            if model is None:
                model = self.config.anthropic_model_sonnet

            data = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": message}],
            }

            url = "https://api.anthropic.com/v1/messages"
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to send message to Anthropic API: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required configuration or secret: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in send_message: {e}")

    def get(self, request: AnthropicRequest) -> AnthropicResponse:
        try:
            data = request.model_dump(exclude_none=True)
            url = "https://api.anthropic.com/v1/messages"
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            response_data = response.json()

            resp = AnthropicResponse(**response_data)
            return resp
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to send request to Anthropic API: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in get method: {str(e)}")

    def count_tokens(self, message: str, model: str = None):
        # Use provided model or default to config model
        if model is None:
            model = self.config.anthropic_model_sonnet

        data = {"model": model, "messages": [{"role": "user", "content": message}]}

        url = "https://api.anthropic.com/v1/messages/count_tokens"
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()

        result = response.json()
        return result["input_tokens"]

    def generate_prompt(
        self, task: str, target_model: str = None
    ) -> PromptGenerateResponse:
        """
        Generate an optimized prompt using Anthropic's experimental prompt tools API.

        This method utilizes Anthropic's closed research preview API to automatically
        generate high-quality prompts based on a task description. The API creates
        structured prompts suitable for use with Claude models.

        Args:
            task (str): Description of the prompt's purpose
                Example: "a chef for a meal prep planning service"
            target_model (str, optional): Target model for optimization
                Example: "claude-3-7-sonnet-20250219"

        Returns:
            PromptGenerateResponse: Response object containing:
                - messages: List of message objects for use with Messages API
                  - User message with generated prompt text
                  - Optional assistant message with response guidance
                - system: System prompt (currently always empty string)
                - usage: Token usage statistics (input/output tokens)

        Raises:
            RuntimeError: If API request fails or network issues occur
            ValueError: If required configuration/secrets are missing
            requests.HTTPError: If API returns error status codes

        Example:
            >>> response = anthropic_mcp.generate_prompt("a helpful programming assistant")
            >>> prompt_text = response.messages[0].content[0].text
            >>> print(f"Generated prompt: {prompt_text}")

        Note:
            - This is an experimental API in closed research preview
            - Access requires explicit invitation from Anthropic
            - Requires anthropic-beta header: "prompt-tools-2025-04-02"
            - No long-term support guarantees for experimental features
            - Designed primarily for prompt engineering platforms

        API Documentation:
            https://docs.anthropic.com/en/api/prompt-tools-generate
        """
        url = "https://api.anthropic.com/v1/experimental/generate_prompt"

        # Format the task string as a dict for the API
        data = {"task": task}
        if target_model:
            data["target_model"] = target_model

        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return PromptGenerateResponse(**response.json())

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to generate prompt from Anthropic API: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required configuration or secret: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in generate_prompt: {e}")

    def improve_prompt(self, data: dict) -> PromptImproveResponse:
        url = "https://api.anthropic.com/v1/experimental/improve_prompt"

        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            result = response.json()
            # Handle usage being returned as dict instead of list
            if isinstance(result.get("usage"), dict):
                result["usage"] = [result["usage"]]
            return PromptImproveResponse(**result)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to generate prompt from Anthropic API: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required configuration or secret: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in generate_prompt: {e}")

    def templatize_prompt(self, data: dict) -> PromptTemplatizeResponse:
        url = "https://api.anthropic.com/v1/experimental/templatize_prompt"

        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            result = response.json()
            # Handle usage being returned as dict instead of list
            if isinstance(result.get("usage"), dict):
                result["usage"] = [result["usage"]]
            return PromptTemplatizeResponse(**result)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to templatize prompt from Anthropic API: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required configuration or secret: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in templatize_prompt: {e}")
