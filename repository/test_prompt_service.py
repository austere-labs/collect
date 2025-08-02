import pytest
from typing import List
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


def create_test_prompts(prompt_service: PromptService) -> List[Prompt]:
    prompt_content = """
    this is a test prompt for testing database persistence... blah blah
    """

    def new_cmd_prompt(prompt_content: str) -> Prompt:
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

    def new_plan_prompt(prompt_content: str) -> Prompt:
        return prompt_service.new_prompt_model(
            prompt_content=prompt_content,
            name="test_prompt.md",
            prompt_type=PromptType.PLAN,
            cmd_category=None,
            status=PromptPlanStatus.APPROVED,
            project="collect",
            description="A basic prd prompt",
            tags=["test", "python", "plan"]
        )
    return [new_cmd_prompt(prompt_content), new_plan_prompt(prompt_content)]


def test_save_prompt_in_db(prompt_service: PromptService):
    # create test cmd and plan prompt types
    pls = create_test_prompts(prompt_service)
    cmd_prompt = pls[0]
    plan_prompt = pls[1]

    try:
        # save test prompts in sqlite and verify success
        cmd_result = prompt_service.save_prompt_in_db(cmd_prompt)
        print(f"cmd_result: {cmd_result}")
        assert cmd_result.success is not False

        plan_result = prompt_service.save_prompt_in_db(plan_prompt)
        print(f"plan_result: {plan_result}")
        assert plan_result.success is not False

        # retrieve the saved test prompts from sqlite and verify they
        # match the original test cmd and plan prompts
        print(f"Retrieving cmd prompt with id: {cmd_prompt.id}")
        retrieved_cmd = prompt_service.get_prompt_by_id(cmd_prompt.id)
        print(f"Retrieved cmd: {retrieved_cmd}")
        assert retrieved_cmd is not None

        retrieved_plan = prompt_service.get_prompt_by_id(plan_prompt.id)
        assert retrieved_plan is not None

        # update prompt and increment the version
        updated_text = cmd_prompt.data.content + "UPDATED TEXT"
        cmd_prompt.data.content = updated_text

        update_result = prompt_service.update_prompt_in_db(cmd_prompt)
        assert update_result.success is True

        # retrieve the updated prompt again from the prompt table and
        # validate the changes were persisted/updated
        retrieved_prompt = prompt_service.get_prompt_by_id(cmd_prompt.id)
        assert retrieved_prompt.data.content == updated_text

        # retrieve the prompt by name
        # and validate correct prompt retrieval
        retrieved_prompt_by_name = prompt_service.get_prompt_by_name(
            cmd_prompt.name)
        assert retrieved_prompt_by_name is not None
        assert retrieved_prompt_by_name.id == cmd_prompt.id

    finally:
        # Clean up test data - this will ALWAYS run, even if test fails
        print("\nCleaning up test prompts...")

        cmd_cleanup = delete_prompt_completely(prompt_service, cmd_prompt.id)
        print(f"CMD cleanup result: {cmd_cleanup}")

        plan_cleanup = delete_prompt_completely(prompt_service, plan_prompt.id)
        print(f"PLAN cleanup result: {plan_cleanup}")


def delete_prompt_completely(prompt_service: PromptService, prompt_id: str):
    """
    DELETE a prompt from tables: prompt, prompt_history and prompt_metrics
    THIS IS FOR INTEGRATION TESTING ONLY - as production code should reserve
    history
    """
    cursor = prompt_service.conn.cursor()
    try:
        # start transaction
        cursor.execute("BEGIN TRANSACTION")

        # delete from prompt_history first (due to composite primary key)
        cursor.execute("""
                       DELETE FROM prompt_history
                       WHERE id = ?
                       """, (prompt_id,))
        prompt_history_rows_deleted = cursor.rowcount

        # delete from prompt_metrics table if any exist
        cursor.execute("""
                       DELETE FROM prompt_metrics
                       WHERE prompt_id = ?
                       """, (prompt_id,))
        prompt_metrics_rows_deleted = cursor.rowcount

        # delete from prompt table (we do this last)
        cursor.execute("""
                       DELETE FROM prompt
                       WHERE id = ?
                       """, (prompt_id,))
        prompt_rows_deleted = cursor.rowcount

        prompt_service.conn.commit()
        return {
            "success": True,
            "prompt_rows": prompt_rows_deleted,
            "prompt_history_rows": prompt_history_rows_deleted,
            "prompt_metrics_rows": prompt_metrics_rows_deleted
        }

    except Exception as e:
        prompt_service.conn.rollback()
        return {
            "success": False,
            "error": str(e)
        }


def test_prompt_loading(prompt_service: PromptService):
    cmds = prompt_service.load_cmds_from_disk()
    print(f"\nTotal commands loaded: {len(cmds.loaded_prompts)}")
    assert len(cmds.errors) == 0

    plans = prompt_service.load_plans_from_disk()
    print(f"\nTotal plans loaded: {len(plans.loaded_prompts)}")
    assert len(plans.errors) == 0

    prompts = cmds.loaded_prompts + plans.loaded_prompts

    results = prompt_service.bulk_save_in_db(prompts)

    bad_results = [result for result in results if not result.success]
    good_results = [result for result in results if result.success]

    print(f"\nGood Result count: {len(good_results)}")
    print(f"\nBad Result count: {len(bad_results)}")
