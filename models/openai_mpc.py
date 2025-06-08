from config import Config
from secret_manager import SecretManager
import requests
import tiktoken


class OpenAIMCP:
    def __init__(
        self,
        config: Config,
        secret_mgr: SecretManager,
        model: str,
    ) -> None:
        self.config = config
        self.secret_mgr = secret_mgr
        self.model = model

    def get_model_list(self) -> list:
        try:
            openai_key = self.secret_mgr.get_secret(self.config.openai_api_key_path)

            headers = {"Authorization": f"Bearer {openai_key}"}

            response = requests.get("https://api.openai.com/v1/models", headers=headers)
            response.raise_for_status()

            model_data = response.json()
            name_list = [model["id"] for model in model_data["data"]]

            return name_list

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to get model list from OpenAI API: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required configuration or secret: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in get_model_list: {e}")

    def extract_text(self, response) -> str:
        """Extract text from OpenAI response format."""
        if not isinstance(response, dict):
            return str(response)

        # OpenAI format
        if "choices" in response:
            choices = response["choices"]
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "")

        return str(response)

    def send_message(
        self, message: str, max_tokens: int = 1024, model: str = None
    ) -> dict:
        try:
            openai_key = self.secret_mgr.get_secret(self.config.openai_api_key_path)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_key}",
            }

            # Use provided model or default
            if model is None:
                model = "gpt-4o"

            # Use max_completion_tokens for reasoning models (o3, o1 series)
            if model and ("o3" in model or "o1" in model):
                data = {
                    "model": model,
                    "max_completion_tokens": max_tokens,
                    "messages": [{"role": "user", "content": message}],
                }
            else:
                data = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": message}],
                }

            url = "https://api.openai.com/v1/chat/completions"
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to send message to OpenAI API: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required configuration or secret: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in send_message: {e}")

    def count_tokens(self, message: str, model: str = None) -> int:
        try:
            # Use provided model or default
            if model is None:
                model = "gpt-4o"

            # OpenAI doesn't have a direct token counting API, so use tiktoken
            enc = tiktoken.encoding_for_model(model)
            return len(enc.encode(message))

        except Exception as e:
            raise RuntimeError(f"Failed to count tokens: {e}")
