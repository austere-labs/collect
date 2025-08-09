**Collect** is a command-line toolkit built with Python that functions as an MCP (Model Context Protocol) server. It is designed to assist with AI-driven development by providing tools to fetch web content, process it, and coordinate analysis across multiple AI models.

*   **Multi-Model Integration**: Interact with models from Google (Gemini), Anthropic (Claude), OpenAI (GPT), and XAI (Grok) through a single interface.
*   **Content Processing**: Fetch content from URLs and convert HTML to clean markdown or plain text.
*   **Code & Diff Analysis**: Perform code reviews on files or git diffs using any of the integrated AI models.
*   **Secure Configuration**: Utilizes Google Cloud Secret Manager for API key storage.
*   **Prompt Management**: A version-controlled system for managing and synchronizing prompts between the local filesystem and a SQLite database.
*   **Token Utilities**: Tools to count token usage for various models to manage costs and context windows.

### MCP Server Configuration

#### For Claude Code

To enable Claude Code to use the `collect` MCP server, create a `.mcp.json` file in your project's root directory:

1.  **Create the Configuration File**: In the root of your project where you want to use the collect tools, create a file named `.mcp.json`.
2.  **Add Configuration**: Add the following JSON configuration:

```json
{
  "mcpServers": {
    "collect": {
      "command": "/path/to/.local/bin/uv",
      "args": [
        "--directory",
        "/path/to/collect",
        "run",
        "collect.py"
      ]
    }
  }
}
```

Replace `/path/to/.local/bin/uv` with the full path to your `uv` binary (you can find this with `which uv`), and `/path/to/collect` with the full path to your collect repository.

#### For Gemini CLI

To enable the Gemini CLI to automatically start the `collect` MCP server, you need to configure a `.gemini/settings.json` file in your project's root directory:

1.  **Create the Directory**: If it doesn't already exist, create a `.gemini` directory in the root of the `collect` project.
2.  **Create the Settings File**: Inside the `.gemini` directory, create a file named `settings.json`.
3.  **Add Configuration**: Paste the following JSON configuration into the `settings.json` file.

```json
{
  "mcpServers": {
    "collect": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "collect.py"
      ],
      "workingDirectory": "/Users/benjaminmetz/python/collect",
      "enabled": true
    }
  }
}
```

This configuration tells the Gemini CLI how to launch the `collect` server, specifying the command, arguments, and working directory.

### Command Category System

The command category system dynamically creates categories based on subdirectories configured in the `.env` file. This approach allows for easy extension of command categories without code changes.

#### How Categories Are Created

1. **Configuration**: Command subdirectories are defined in the `.env` file:
   ```
   COMMAND_SUBDIRS=archive,go,js,mcp,python,tools
   ```

2. **Dynamic Enum Generation**: The `create_cmd_category_enum()` function in `repository/prompt_models.py` reads the `COMMAND_SUBDIRS` from the `.env` file via the `Config` class and dynamically creates a `CmdCategory` enum at runtime.

3. **Directory Management**: When the `PromptService` initializes, the `cmd_check_dirs()` function in `repository/prompt_service.py`:
   - Reads the subdirectory list from the config
   - Checks for the existence of each configured subdirectory under both `.claude/commands/` and `.gemini/commands/`
   - Automatically creates any missing directories
   - Each subdirectory becomes a valid command category

4. **Category Assignment**: When loading commands from disk:
   - Files directly in `.claude/commands/` or `.gemini/commands/` are assigned the `UNCATEGORIZED` category
   - Files in subdirectories are assigned the category matching the subdirectory name
   - The category is stored as part of the prompt's metadata in the database

#### Adding New Categories

To add new command categories:
1. Update the `COMMAND_SUBDIRS` line in the `.env` file with your new category
2. The system will automatically create the directories and recognize them as valid categories on the next run
3. Commands placed in those directories will be tagged with the new category

#### Example

To add a "rust" category:
1. Edit `.env`:
   ```
   COMMAND_SUBDIRS=archive,go,js,mcp,python,tools,rust
   ```
2. Restart the service or run the prompt service
3. The system will create:
   - `.claude/commands/rust/`
   - `.gemini/commands/rust/`
4. Any `.md` files placed in these directories will be categorized as "rust" commands

#### Current Directory Structure
Based on the `.env` configuration (`COMMAND_SUBDIRS=archive,go,js,mcp,python,tools`), the directory structure is:

```
.claude/
└── commands/
    ├── archive/          # Archived commands
    ├── go/               # Go-specific commands
    ├── js/               # JavaScript commands
    ├── mcp/              # MCP server commands
    ├── python/           # Python-specific commands
    └── tools/            # Tool-related commands

.gemini/
└── commands/
    ├── archive/
    ├── go/
    ├── js/
    ├── mcp/
    ├── python/
    └── tools/
```

Note: Files placed directly in `.claude/commands/` or `.gemini/commands/` (not in subdirectories) are automatically assigned the `UNCATEGORIZED` category.

### Prompt Management System

The project includes a system for managing prompts **that is very much under construction**. Prompts are categorized as either **Commands** (`CMD`) or **Plans** (`PLAN`). This system, located in the `repository/` directory, uses a SQLite database to store and version prompts, while also synchronizing them with the local filesystem.

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
