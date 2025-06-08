from config import Config
from secret_manager import SecretManager
import requests


class XaiMCP:
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
        xai_key = self.secret_mgr.get_secret(self.config.xai_api_key_path)

        headers = {
            "Authorization": f"Bearer {xai_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get("https://api.x.ai/v1/models", headers=headers)
            response.raise_for_status()
            data = response.json()

            name_list = [model["id"] for model in data["data"]]
            return name_list

        except Exception as e:
            print(f"Error fetching XAI models: {str(e)}")
            return []

    def extract_text(self, response) -> str:
        """Extract text from XAI response format."""
        if not isinstance(response, dict):
            return str(response)

        # XAI format (same as OpenAI)
        if "choices" in response:
            choices = response["choices"]
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "")

        return str(response)

    def send_message(
        self, message: str, model: str = None, reasoning_effort: str = "high"
    ):
        try:
            xai_key = self.secret_mgr.get_secret(self.config.xai_api_key_path)

            headers = {
                "Authorization": f"Bearer {xai_key}",
                "Content-Type": "application/json",
            }

            # Use provided model or default to config model
            if model is None:
                model = "grok-3-mini-fast-latest"

            data = {
                "messages": [
                    {"role": "system", "content": self.config.grok_system_prompt},
                    {"role": "user", "content": message},
                ],
                "reasoning_effort": reasoning_effort,
                "model": model,
            }

            url = "https://api.x.ai/v1/chat/completions"
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to send message to XAI: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required configuration or secret: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in send_message: {e}")

    def count_tokens(self, text: str, model: str = None):
        xai_key = self.secret_mgr.get_secret(self.config.xai_api_key_path)

        headers = {
            "Authorization": f"Bearer {xai_key}",
            "Content-Type": "application/json",
        }

        # Use provided model or default to config model
        if model is None:
            model = "grok-3-fast-latest"

        data = {"model": model, "text": text}

        url = "https://api.x.ai/v1/tokenize-text"
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        return len(result["token_ids"])
