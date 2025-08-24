from dotenv import load_dotenv
import os


class Config:
    # Load .env for configuration
    load_dotenv(".env")

    def __init__(self) -> None:
        # Core configuration
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.port = os.getenv("PORT")
        self.base_api_url = os.getenv("BASE_API_URL")
        self.db_path = os.getenv("DB_PATH")

        # Anthropic configuration
        self.anthropic_key_path = os.getenv("ANTHROPIC_API_KEY_PATH")
        self.anthropic_model_opus = os.getenv("ANTHROPIC_MODEL_OPUS")
        self.anthropic_model_sonnet = os.getenv("ANTHROPIC_MODEL_SONNET")

        # Gemini configuration
        self.gemini_api_key_path = os.getenv("GEMINI_API_KEY_PATH")
        self.gemini_base_url = os.getenv("GEMINI_BASE_URL")

        # XAI/Grok configuration
        self.xai_api_key_path = os.getenv("XAI_API_KEY_PATH")
        self.grok_system_prompt = os.getenv("GROK_SYSTEM_PROMPT")

        # OpenAI configuration
        self.openai_api_key_path = os.getenv("OPENAI_API_KEY_PATH")

        # Code review model configuration
        self.openai_default_code_review_model = os.getenv(
            "OPENAI_DEFAULT_CODE_REVIEW_MODEL"
        )
        self.gemini_default_code_review_model = os.getenv(
            "GEMINI_DEFAULT_CODE_REVIEW_MODEL"
        )
        self.anthropic_default_code_review_model = os.getenv(
            "ANTHROPIC_DEFAULT_CODE_REVIEW_MODEL"
        )
        self.xai_default_code_review_model = os.getenv(
            "XAI_DEFAULT_CODE_REVIEW_MODEL")

        # GitHub configuration
        self.github_url = os.getenv("GITHUB_URL")

        # Command subdirectories - read as comma-separated string
        command_subdirs_str = os.getenv(
            "COMMAND_SUBDIRS", "archive,go,js,mcp,python,tools"
        )
        self.command_subdirs = [
            subdir.strip() for subdir in command_subdirs_str.split(",")
        ]
