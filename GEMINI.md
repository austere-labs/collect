# Gemini Code Assistant Context

This document provides context for the Gemini Code Assistant to understand the project structure, conventions, and important files.

## Project Overview

This project is a Python-based MCP (Model Context Protocol) server named "Collect". Its primary purpose is to fetch web content, process it, and facilitate multi-model AI analysis workflows. It provides a unified interface to interact with various AI models (OpenAI, Anthropic, Gemini, XAI) for tasks like code review. The server is built using the `mcp` library and exposes several tools for fetching URLs, converting HTML to markdown, counting tokens, and more. It also includes a database layer using SQLite for data persistence.

**Key Technologies:**

*   **Programming Language:** Python
*   **Framework:** `mcp` (Model Context Protocol)
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

*   **Testing:** Tests are written using `pytest` and are located in files like `test_collect.py`. Asynchronous functions are tested using `@pytest.mark.asyncio`. The project uses `pytest-xdist` for parallel test execution.
*   **Linting and Formatting:** The project uses `ruff` for linting and `black` for formatting. These are run via the `Makefile`.
*   **Configuration:** Project configuration is managed in `config.py`, which loads environment variables from a `.env` file.
*   **Secrets Management:** API keys and other secrets are managed through Google Cloud Secret Manager, as indicated in `secret_manager.py` and `config.py`.
*   **Database:** The project uses SQLite for its database. The database connection logic is in `repository/database.py`. Migrations are handled by `yoyo-migrations`.

## Key Files

*   **`collect.py`:** The main entry point of the MCP server. It defines the available tools, such as `fetch_urls`, `run_code_review`, and `to_markdown`.
*   **`pyproject.toml`:** Defines the project's dependencies and development tool configurations.
*   **`Makefile`:** Provides convenient commands for common development tasks like testing, linting, and formatting.
*   **`config.py`:** Handles the project's configuration by loading environment variables from a `.env` file.
*   **`reviewer/code_review.py`:** Contains the logic for the code review functionality. It takes a diff file, sends it to multiple LLMs, and then formats and saves the results.
*   **`models/`:** This directory contains modules for interacting with different AI models (e.g., `anthropic_mpc.py`, `openai_mpc.py`).
*   **`repository/database.py`:** Contains the logic for connecting to the SQLite database.
*   **`migrations/`:** This directory contains the SQL migration files for the database schema.
