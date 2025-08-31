import marimo

__generated_with = "0.14.12"
app = marimo.App(width="medium")


@app.cell
def _():
    from agents.tomlagent import markdown_to_toml_gemini_tool
    from models.anthropic_models import AnthropicRequest, Message, ToolChoice
    from models.anthropic_mpc import AnthropicMCP
    from config import Config
    from secret_manager import SecretManager

    return (
        AnthropicMCP,
        AnthropicRequest,
        Config,
        Message,
        SecretManager,
        ToolChoice,
        markdown_to_toml_gemini_tool,
    )


@app.cell
def _(AnthropicMCP, Config, SecretManager):
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    sonnet = config.anthropic_model_sonnet
    anthropic_client = AnthropicMCP(config, secret_mgr, sonnet)
    return anthropic_client, sonnet


@app.cell
def _():
    from typing import Optional
    from pathlib import Path

    def read_file(file_path: str, encoding: str = "utf-8") -> Optional[str]:
        try:
            return Path(file_path).read_text(encoding=encoding)
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            print(f"Error reading file {file_path}: {str(e)}")
            return None

    return (read_file,)


@app.cell
def _(read_file):
    markdown_file = read_file(".claude/commands/example.md")
    return (markdown_file,)


@app.cell
def _(markdown_file):
    print(markdown_file)
    return


@app.cell
def _(Message, markdown_file):
    toml_prompt = f"""
    <INSTRUCTIONS>
    Please convert the the `markdown_file` to TOML format.
    </INSTRUCTIONS>
    {markdown_file}
    """
    message = Message(role="user", content=toml_prompt)
    return (message,)


@app.cell
def _(
    AnthropicRequest,
    ToolChoice,
    markdown_to_toml_gemini_tool,
    message,
    sonnet,
):
    req = AnthropicRequest(
        model=sonnet,
        max_tokens=1024,
        messages=[message],
        tools=[markdown_to_toml_gemini_tool],
        tool_choice=ToolChoice(type="auto"),
    )
    return (req,)


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
