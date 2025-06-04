from config import Config
from secret_manager import SecretManager
from models.anthropic_prompt_generate import PromptGenerateResponse
from models.anthropic_prompt_improve import PromptImproveResponse
from models.anthropic_prompt_templatize import PromptTemplatizeResponse

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
        anthropic_key = self.secret_mgr.get_secret(
            self.config.anthropic_key_path)

        return {
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "prompt-tools-2025-04-02",
        }

    def get_model_list(self):
        response = requests.get(
            "https://api.anthropic.com/v1/models",
            headers=self.headers)
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
        self,
        message: str,
        max_tokens: int = 1024,
        model: str = None
    ) -> dict:
        try:
            # Use provided model or default to config model
            if model is None:
                model = self.config.anthropic_model_sonnet

            data = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "user", "content": message}
                ]
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

    def count_tokens(self, message: str, model: str = None):
        # Use provided model or default to config model
        if model is None:
            model = self.config.anthropic_model_sonnet

        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": message}
            ]
        }

        url = "https://api.anthropic.com/v1/messages/count_tokens"
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()

        result = response.json()
        return result["input_tokens"]

    def generate_prompt(self, data: dict) -> PromptGenerateResponse:
        url = "https://api.anthropic.com/v1/experimental/generate_prompt"

        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return PromptGenerateResponse(**response.json())

        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Failed to generate prompt from Anthropic API: {e}")
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
            if isinstance(result.get('usage'), dict):
                result['usage'] = [result['usage']]
            return PromptImproveResponse(**result)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Failed to generate prompt from Anthropic API: {e}")
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
            if isinstance(result.get('usage'), dict):
                result['usage'] = [result['usage']]
            return PromptTemplatizeResponse(**result)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Failed to templatize prompt from Anthropic API: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required configuration or secret: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in templatize_prompt: {e}")