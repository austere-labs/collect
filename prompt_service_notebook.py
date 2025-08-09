import marimo

__generated_with = "0.14.12"
app = marimo.App(width="medium")


@app.cell
def _():
    from repository.database import SQLite3Database
    from repository.prompt_service import PromptService
    from repository.prompt_models import (
        Prompt,
        PromptType,
        PromptPlanStatus,
        CmdCategory,
    )

    return (
        CmdCategory,
        Prompt,
        PromptPlanStatus,
        PromptService,
        PromptType,
        SQLite3Database,
    )


@app.cell
def _(PromptService, SQLite3Database):
    db = SQLite3Database("data/collect.db")
    with db.get_connection() as conn:
        ps = PromptService(conn)
    return (ps,)


@app.cell
def _(ps):
    cmds = ps.load_cmds_from_disk()
    plans = ps.load_plans_from_disk()
    return cmds, plans


@app.cell
def _(cmds):
    print(f"Num cmds: {len(cmds.loaded_prompts)}\n")
    for cmd in cmds.loaded_prompts:
        print(cmd.name)
    return


@app.cell
def _(plans):
    print(f"Num plans: {len(plans.loaded_prompts)}\n")
    for plan in plans.loaded_prompts:
        print(plan.name)
    return


@app.cell
def _():
    db_name = "collect_completed_add_claude_sdk_processing.md"
    result = db_name.split("_")
    print(result)
    return db_name, result


@app.cell
def _(result):
    print(f"project name: {result[0]}")
    print(f"plan status: {result[1]}")
    return


@app.cell
def _(result):
    namelist = result[2:]
    print(namelist)
    return (namelist,)


@app.cell
def _(namelist):
    newname = ""
    for word in namelist:
        if not word.endswith(".md"):
            newname = newname + word + "_"
        else:
            newname = newname + word
    print(newname)
    return


@app.cell
def _(db_name):
    print(db_name.split("_")[2:])
    return


@app.cell
def _(PromptType):
    def parse_db_name(db_name: str, prompt_type: PromptType) -> str:
        ls = db_name.split("_")
        filename = ""
        if prompt_type == PromptType.PLAN:
            project = ls[0]
            plan_status = ls[1]
            print(f"project: {project}")
            print(f"plan status: {plan_status}")

            for word in ls[2:]:
                if not word.endswith(".md"):
                    filename = filename + word + "_"
                else:
                    filename = filename + word
            print(f"file name: {filename}")

            return filename

        if prompt_type == PromptType.CMD:
            cmd_dir = ls[0]
            print(f"cmd/dir: {cmd_dir}")
            for word in ls[1:]:
                if not word.endswith(".md"):
                    filename = filename + word + "_"
                else:
                    filename = filename + word
            print(f"file name: {filename}")

            return filename

    return (parse_db_name,)


@app.cell
def _(PromptType, db_name, parse_db_name):
    parse_db_name(db_name, PromptType.PLAN)
    return


@app.cell
def _(PromptType, parse_db_name):
    parse_db_name("tools_create_database.md", PromptType.CMD)
    return


@app.cell
def _(CmdCategory, Prompt, PromptPlanStatus, PromptType, ps):
    def new_cmd_prompt(prompt_content: str) -> Prompt:
        return ps.new_prompt_model(
            prompt_content=prompt_content,
            name="test_prompt.md",
            prompt_type=PromptType.CMD,
            cmd_category=CmdCategory.PYTHON,
            status=PromptPlanStatus.DRAFT,
            project="collect",
            description="A basic test prompt",
            tags=["test", "python", "cmd"],
        )

    def new_plan_prompt(prompt_content: str) -> Prompt:
        return ps.new_prompt_model(
            prompt_content=prompt_content,
            name="test_prompt.md",
            prompt_type=PromptType.PLAN,
            cmd_category=None,
            status=PromptPlanStatus.APPROVED,
            project="collect",
            description="A basic prd prompt",
            tags=["test", "python", "plan"],
        )

    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
