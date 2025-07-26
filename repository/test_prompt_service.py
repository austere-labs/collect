import pytest
from repository.database import SQLite3Database
from repository.prompt_service import PromptService
from repository.prompt_models import (
    Prompt,
    PromptType,
    PromptPlanStatus,
    CmdCategory
)


@pytest.fixture
def prompt_service():
    """
    ## How It Works

    1. **`with db.get_connection() as conn:`**
       - Opens a database connection using a context manager
       - The `as conn` assigns the connection to the variable
       - When the `with` block exits, `conn.close()` is automatically called

    2. **`cmd_service = CmdsService(conn)`**
       - Creates the service object with the database connection
       - The service can now execute database operations

    3. **`yield cmd_service`**
       - This is pytest fixture syntax that provides the service to the test
       - `yield` pauses execution here while the test runs
       - After the test completes, execution resumes after the `yield`

    4. **Automatic cleanup**
       - When the test finishes, the `with` block exits
       - Database connection is automatically closed
       - Resources are freed

    This pattern ensures **deterministic cleanup** -
    the database connection will always be properly closed regardless of
    whether the test passes or fails.
    """
    db = SQLite3Database(db_path="data/collect.db")
    with db.get_connection() as conn:
        cmd_service = PromptService(conn)

        yield cmd_service


def test_check_dirs(prompt_service: PromptService):
    result = prompt_service.cmd_check_dirs()
    assert result is True


def test_load_cmds_from_disk(prompt_service: PromptService):
    load_results = prompt_service.load_cmds_from_disk()
    # Assert no errors occurred during loading
    assert load_results.errors is None or len(load_results.errors) == 0, \
        f"Expected no errors, but found {
            len(load_results.errors) if load_results.errors else 0} errors"


def test_load_plans_from_disk(prompt_service: PromptService):
    load_results = prompt_service.load_plans_from_disk()

    print(f"\nTotal plans loaded: {len(load_results.loaded_prompts)}")
    # Assert no errors occurred during loading
    assert load_results.errors is None or len(load_results.errors) == 0, \
        f"Expected no errors, but found {
            len(load_results.errors) if load_results.errors else 0} errors"


def create_test_prompt(prompt_service: PromptService) -> Prompt:
    """Create a simple prompt example for testing using
    cmd_service.new_prompt_model

    Args:
        cmd_service: CmdsService instance to use for creating the prompt

    Returns:
        Prompt: A test prompt with basic data
    """
    prompt_content = """
        # Test Prompt
        This is a simple test prompt for validation.
    """

    return prompt_service.new_prompt_model(
        prompt_content=prompt_content,
        name="test_prompt.md",
        prompt_type=PromptType.CMD,
        cmd_category=CmdCategory.PYTHON,
        status=PromptPlanStatus.DRAFT,
        project="collect",
        description="A basic test prompt",
        tags=["test", "python", "cmd"]
    )


def test_cmd_loading(prompt_service: PromptService):
    cmds = prompt_service.load_cmds_from_disk()
    print(f"\nTotal commands loaded: {len(cmds.loaded_prompts)}")
    assert len(cmds.errors) == 0

    for cmd in cmds.loaded_prompts:
        print(f"Full name in DB: {cmd.name}")
        print(f"  Category: {cmd.data.cmd_category}")
        # Extract just filename from the db_name
        # db_name format is: category_filename.md
        filename_only = cmd.name.split(
            '_', 1)[1] if '_' in cmd.name else cmd.name
        print(f"  Filename only: {filename_only}")
        print("---")

    plans = prompt_service.load_plans_from_disk()
    print(f"\nTotal plans loaded: {len(plans.loaded_prompts)}")
    assert len(plans.errors) == 0

    for plan in plans.loaded_prompts:
