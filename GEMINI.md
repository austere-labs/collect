# Gemini Code Assistant Context

This document provides context for the Gemini Code Assistant to understand the project structure, conventions, and important files.

## Project Overview

This project is a Python-based MCP (Model Context Protocol) server named "Collect". Its primary purpose is to fetch web content, process it, and facilitate multi-model AI analysis workflows. It provides a unified interface to interact with various AI models (OpenAI, Anthropic, Gemini, XAI) for tasks like code review, documentation extraction, and prompt generation.

The server is built using the `mcp` library and exposes several tools, including:
*   **Code Review:** `run_code_review` and `run_git_diff_review` for running code analysis using multiple LLMs.
*   **Web Fetching:** `fetch_urls`, `fetch_url`, and `get_docs` for retrieving and extracting content from web pages.
*   **Content Processing:** `to_markdown` and `strip_html` for converting HTML to other formats.
*   **AI Model Interaction:** Tools to list available models (`get_anthropic_model_list`, etc.) and count tokens (`count_openai_tokens`, etc.).
*   **Prompt Engineering:** `generate_prompt` leverages Anthropic's experimental API to create optimized prompts from simple descriptions.
*   **System Tools:** `copy_clipboard` for clipboard integration.

The project also includes a database layer using SQLite for data persistence and an associated FastAPI server (`api.py`) for related functionalities.

## Key Technologies

*   **Programming Language:** Python
*   **Framework:** `mcp` (Model Context Protocol), FastAPI
*   **Key Libraries:**
    *   `httpx` for asynchronous HTTP requests.
    *   `anthropic`, `openai`, `google-cloud-aiplatform` for interacting with various LLMs.
    *   `readabilipy`, `markdownify`, `beautifulsoup4` for HTML processing.
    *   `pyperclip` for clipboard integration.
    *   `yoyo-migrations` for database schema management.
*   **Package Manager:** `uv`
*   **Testing:** `pytest` with `pytest-asyncio` and `pytest-xdist` for parallel testing.
*   **Linting/Formatting:** `ruff` and `black`.
*   **Database:** SQLite.

## Building and Running

*   **Install Dependencies:** `uv sync`
*   **Run the Server:** `python collect.py`
*   **Run Tests:** `uv run pytest -v -s -n auto`
*   **Run Linter:** `ruff check .`
*   **Run Formatter:** `black .`
*   **Apply Database Migrations:** `uv run yoyo apply --config yoyo.ini --batch`

## Development Conventions

*   **Testing:** Tests are written using `pytest` and are located in files like `test_collect.py` and `test_generate_prompt.py`. Asynchronous functions are tested using `@pytest.mark.asyncio`.
*   **Linting and Formatting:** The project uses `ruff` for linting and `black` for formatting.
*   **Configuration:** Project configuration is managed in `config.py`, which loads environment variables from a `.env` file.
*   **Secrets Management:** API keys and other secrets are managed through Google Cloud Secret Manager, as indicated in `secret_manager.py` and `config.py`.
*   **Database:** The project uses SQLite for its database. The database connection logic is in `repository/database.py`. Migrations are handled by `yoyo-migrations`.

## Key Files

*   **`collect.py`:** The main entry point of the MCP server. It defines the available tools.
*   **`api.py`:** A FastAPI server that runs alongside the MCP server.
*   **`pyproject.toml`:** Defines the project's dependencies and development tool configurations.
*   **`config.py`:** Handles the project's configuration by loading environment variables.
*   **`reviewer/code_review.py`:** Contains the logic for the code review functionality.
*   **`models/`:** This directory contains modules for interacting with different AI models (e.g., `anthropic_mpc.py`, `openai_mpc.py`).
*   **`repository/`:** Contains database models, services, and connection logic.
*   **`migrations/`:** Contains the SQL migration files for the database schema.
*   **`test_*.py`:** Test files for the project, such as `test_collect.py` and `test_generate_prompt.py`.
