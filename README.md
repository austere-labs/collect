**Collect** is a command-line toolkit built with Python that functions as an MCP (Model Context Protocol) server. It is designed to assist with AI-driven development by providing tools to fetch web content, process it, and coordinate analysis across multiple AI models.

*   **Multi-Model Integration**: Interact with models from Google (Gemini), Anthropic (Claude), OpenAI (GPT), and XAI (Grok) through a single interface.
*   **Content Processing**: Fetch content from URLs and convert HTML to clean markdown or plain text.
*   **Code & Diff Analysis**: Perform code reviews on files or git diffs using any of the integrated AI models.
*   **Secure Configuration**: Utilizes Google Cloud Secret Manager for API key storage.
*   **Prompt Management**: A version-controlled system for managing and synchronizing prompts between the local filesystem and a SQLite database.
*   **Token Utilities**: Tools to count token usage for various models to manage costs and context windows.

### Prompt Management System

The project includes a comprehensive system for managing prompts, which are categorized as either **Commands** (`CMD`) or **Plans** (`PLAN`). This system, located in the `repository/` directory, uses a SQLite database to store and version prompts, while also synchronizing them with the local filesystem.

*   **Core Components**:
    *   `prompt_service.py`: The main service class that orchestrates loading, saving, versioning, and flattening prompts.
    *   `prompt_models.py`: Defines the Pydantic data models for prompts, including `Prompt`, `PromptData`, and various status enums like `PromptType` and `PromptPlanStatus`.
    *   `database.py`: Manages the connection to the `collect.db` SQLite database.
    *   `20250727_01_create-prompt-tables.sql`: The database migration file that defines the schema for the `prompt` and `prompt_history` tables.

*   **Synchronization Workflow**:
    1.  **Loading from Disk**: The `PromptService` can load prompts from predefined directories (`.claude/commands`, `.gemini/commands`, and `_docs/plans`).
    2.  **Database Persistence**: Loaded prompts are saved to the SQLite database. The service checks for existing prompts by name. If a prompt already exists and its content has changed (verified via a SHA256 hash), a new version is created in the `prompt_history` table, and the main `prompt` table is updated.
    3.  **Flattening to Disk**: The service can "flatten" the prompts from the database back to the filesystem, ensuring that the local files are consistent with the database state. This is useful for maintaining a clear and organized prompt library.

*   **Versioning**:
    *   Every time a prompt's content is updated, its `version` number is incremented.
    *   A complete record of all versions is stored in the `prompt_history` table, including a timestamp and a change summary. This allows for a full audit trail of how a prompt has evolved.

This system ensures that prompts are treated as version-controlled assets within the project, providing a structured and auditable way to manage the instructions given to the AI models.
