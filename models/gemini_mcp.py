from config import Config
from secret_manager import SecretManager
import requests
from fetcher import Fetcher
from mcp.server.fastmcp import Context


class GeminiMCP:
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
            gemini_key = self.secret_mgr.get_secret(self.config.gemini_api_key_path)

            base_url = self.config.gemini_base_url
            url = f"{base_url}models?key={gemini_key}"
            response = requests.get(url)
            response.raise_for_status()

            model_data = response.json()
            name_list = [model["name"].split("/")[-1] for model in model_data["models"]]

            return name_list

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to get model list from Gemini API: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required configuration or secret: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in get_model_list: {e}")

    def extract_text(self, ai_response: dict) -> str:
        # Extract text from response
        if "candidates" in ai_response and len(ai_response["candidates"]) > 0:
            candidate = ai_response["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                parts = candidate["content"]["parts"]
                if len(parts) > 0 and "text" in parts[0]:
                    return parts[0]["text"]
        return str(ai_response)

    async def build_prompt_from_url(
        self, url: str, prompt: str, ctx: Context = None
    ) -> str:

        fetcher = Fetcher(ctx)
        response = await fetcher.get(url)
        concat = prompt + response

        ai_response = self.send_message(
            concat, max_tokens=1024, model="gemini-2.5-flash-preview-05-20"
        )

        return self.extract_text(ai_response)

    def send_message(
        self, message: str, max_tokens: int = 1024, model: str = None
    ) -> dict:
        try:
            gemini_key = self.secret_mgr.get_secret(self.config.gemini_api_key_path)

            # Use provided model or default
            if model is None:
                model = "gemini-2.0-flash"

            base_url = self.config.gemini_base_url
            url = f"{base_url}models/{model}:generateContent?key={gemini_key}"

            headers = {"Content-Type": "application/json"}

            data = {
                "contents": [{"parts": [{"text": message}]}],
                "generationConfig": {"maxOutputTokens": max_tokens},
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to send message to Gemini API: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required configuration or secret: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in send_message: {e}")

    def count_tokens(self, message: str, model: str = None) -> int:
        try:
            gemini_key = self.secret_mgr.get_secret(self.config.gemini_api_key_path)

            # Use provided model or default
            if model is None:
                model = "gemini-2.0-flash"

            # Fix common model name errors
            if model == "gemini-2.5-pro-preview":
                model = "gemini-2.5-flash"

            base_url = self.config.gemini_base_url
            url = f"{base_url}models/{model}:countTokens?key={gemini_key}"

            headers = {"Content-Type": "application/json"}

            data = {"contents": [{"parts": [{"text": message}]}]}

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            return result["totalTokens"]

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to count tokens with Gemini API: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required configuration or secret: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in count_tokens: {e}")
