from config import Config
from secret_manager import SecretManager
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

    def get_model_list(self):
        anthropic_key = self.secret_mgr.get_secret(
            self.config.anthropic_key_path)

        headers = {
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01"
        }

        response = requests.get(
            "https://api.anthropic.com/v1/models", headers=headers)
        response.raise_for_status()

        model_data = response.json()
        name_list = [model["id"] for model in model_data["data"]]

        return name_list

    def send_message(
        self,
        message: str,
        max_tokens: int = 1024,
        model: str = None
    ) -> dict:
        try:
            anthropic_key = self.secret_mgr.get_secret(
                self.config.anthropic_key_path)

            headers = {
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

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
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to send message to Anthropic API: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required configuration or secret: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in send_message: {e}")

    def count_tokens(self, message: str, model: str = None):
        anthropic_key = self.secret_mgr.get_secret(
            self.config.anthropic_key_path)

        headers = {
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

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
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        return result["input_tokens"]
