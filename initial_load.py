#!/usr/bin/env python3
"""
Initial load script for loading plans and commands from disk into database
Uses PromptService to load from .claude/commands,
.gemini/commands, and _docs/plans
"""
import sys
from typing import List
from repository.database import SQLite3Database
from repository.prompt_service import PromptService
from repository.prompt_models import PromptLoadResult, PromptCreateResult


def load_commands_to_db(service: PromptService) -> PromptLoadResult:
    """
    Load commands from .claude and .gemini directories and save to database
    This is primarily for an initial load or to clean and restart from disk

    Returns:
        PromptLoadResult: Combined result with loading and saving information
    """
    print("📁 Loading commands from disk...")

    # Load commands from filesystem
    cmd_result: PromptLoadResult = service.load_cmds_from_disk()

    if cmd_result.errors:
        print(f"⚠️  Found {len(cmd_result.errors)
                           } errors while loading commands:")
        for error in cmd_result.errors:
            print(f"   ❌ {error.filename}: {error.error_message}")

    if not cmd_result.loaded_prompts:
        print("ℹ️  No commands found to load")
        return cmd_result

    print(f"Found: {len(cmd_result.loaded_prompts)} to save to database")

    # Save commands to database
    save_results: List[PromptCreateResult] = service.bulk_save_in_db(
        cmd_result.loaded_prompts)

    # Track save results
    save_success_count = 0
    save_errors = []

    for result in save_results:
        if result.success:
            save_success_count += 1
        else:
            print(f"   ❌ Failed to save command: {result.error_message}")
            # Convert PromptCreateResult errors to LoadError format for consistency
            from repository.prompt_models import LoadError
            save_errors.append(LoadError(
                filename=f"database_save_{result.prompt_id}",
                error_message=result.error_message or "Unknown save error",
                error_type=result.error_type or "SaveError"
            ))

    # Return updated PromptLoadResult with combined errors
    all_errors = (cmd_result.errors or []) + save_errors

    return PromptLoadResult(
        loaded_prompts=cmd_result.loaded_prompts,
        errors=all_errors if all_errors else None
    )


def load_plans_to_db(service: PromptService) -> PromptLoadResult:
    """Load plans from _docs/plans directories and save to database

    Returns:
        PromptLoadResult: Combined result with loading and saving information
    """
    print("📋 Loading plans from disk...")

    # Load plans from filesystem
    plan_result: PromptLoadResult = service.load_plans_from_disk()

    if plan_result.errors:
        print(f"⚠️  Found {len(plan_result.errors)
                           } errors while loading plans:")
        for error in plan_result.errors:
            print(f"   ❌ {error.filename}: {error.error_message}")

    if not plan_result.loaded_prompts:
        print("ℹ️  No plans found to load")
        return plan_result

    print(f"📄 Found {len(plan_result.loaded_prompts)
                     } plans to save to database")

    # Save plans to database
    save_results: List[PromptCreateResult] = service.bulk_save_in_db(
        plan_result.loaded_prompts)

    # Track save results
    save_success_count = 0
    save_errors = []

    for result in save_results:
        if result.success:
            save_success_count += 1
        else:
            print(f"   ❌ Failed to save plan: {result.error_message}")
            # Convert PromptCreateResult errors to LoadError format for consistency
            from repository.prompt_models import LoadError
            save_errors.append(LoadError(
                filename=f"database_save_{result.prompt_id}",
                error_message=result.error_message or "Unknown save error",
                error_type=result.error_type or "SaveError"
            ))

    # Return updated PromptLoadResult with combined errors
    all_errors = (plan_result.errors or []) + save_errors

    return PromptLoadResult(
        loaded_prompts=plan_result.loaded_prompts,
        errors=all_errors if all_errors else None
    )


def main():
    """Main function to orchestrate the complete loading process"""
    print("🚀 Starting initial data load from disk to database...")
    print("=" * 60)

    try:
        # Initialize database connection
        database = SQLite3Database("data/prompts.db")

        with database.get_connection() as conn:
            # Create PromptService instance
            service = PromptService(conn)

            # Track overall statistics
            total_loaded = 0
            total_errors = 0

            # Load commands
            cmd_result: PromptLoadResult = load_commands_to_db(service)
            cmd_loaded = len(cmd_result.loaded_prompts)
            cmd_errors = len(cmd_result.errors) if cmd_result.errors else 0

            total_loaded += cmd_loaded
            total_errors += cmd_errors

            print(f"✅ Commands: {cmd_loaded} loaded, {cmd_errors} errors")
            print()

            # Load plans
            plan_result: PromptLoadResult = load_plans_to_db(service)
            plan_loaded = len(plan_result.loaded_prompts)
            plan_errors = len(plan_result.errors) if plan_result.errors else 0

            total_loaded += plan_loaded
            total_errors += plan_errors

            print(f"✅ Plans: {plan_loaded} loaded, {plan_errors} errors")
            print()

            # Print final summary
            print("=" * 60)
            print("📊 FINAL SUMMARY:")
            print(f"   ✅ Total items loaded: {total_loaded}")
            print(f"   ❌ Total errors: {total_errors}")

            if total_errors == 0:
                print("🎉 All data loaded successfully!")
            else:
                print(f"⚠️  Completed with {
                      total_errors} errors - check output above")

    except Exception as e:
        print(f"💥 Fatal error during loading process: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        sys.exit(1)


if __name__ == "__main__":
    main()
