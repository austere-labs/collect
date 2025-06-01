from dotenv import load_dotenv
import os


class Config:
    # Load .env.local first (for local development), then .env (for defaults)
    load_dotenv('.env.local')
    load_dotenv('.env')

    def __init__(self) -> None:
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.anthropic_key_path = os.getenv("ANTHROPIC_API_KEY_PATH")
        self.anthropic_model_opus = os.getenv("ANTHROPIC_MODEL_OPUS")
        self.anthropic_model_sonnet = os.getenv("ANTHROPIC_MODEL_SONNET")
        self.gemini_api_key_path = os.getenv("GEMINI_API_KEY_PATH")
        self.gemini_base_url = os.getenv("GEMINI_BASE_URL")
        self.xai_api_key_path = os.getenv("XAI_API_KEY_PATH")
        self.grok_system_prompt = os.getenv("GROK_SYSTEM_PROMPT")
        self.openai_api_key_path = os.getenv("OPENAI_API_KEY_PATH")
        self.openai_default_code_review_model = os.getenv(
            "OPENAI_DEFAULT_CODE_REVIEW_MODEL")
        self.gemini_default_code_review_model = os.getenv(
            "GEMINI_DEFAULT_CODE_REVIEW_MODEL")
        self.anthropic_default_code_review_model = os.getenv(
            "ANTHROPIC_DEFAULT_CODE_REVIEW_MODEL")
        self.xai_default_code_review_model = os.getenv(
            "XAI_DEFAULT_CODE_REVIEW_MODEL")

        # Direct API Keys (alternative to Secret Manager)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.xai_api_key = os.getenv("XAI_API_KEY")
