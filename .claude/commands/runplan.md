---
allowed-tools: Bash, TodoWrite, TodoList, Read
argument-hint: plan [filepath]
description: Executes approved implementation plans from the _docs/plans/approved/ directory. Validates plan format, creates a todo list for tracking, implements specified changes with strict scope control, runs tests and quality checks, and moves completed plans to the completed/ directory with documentation.
---
## Execute the implementation plan: $ARGUMENTS

### WORKFLOW:

1. **Plan Validation**:
   - Verify the plan exists in `@_docs/plans/approved/` directory
   - If not in approved/, prompt user to move it from drafts/ or update the plan
   - Validate plan follows the documented format from CLAUDE.md
   - Ensure plan contains specific implementation details (file paths, function signatures, error handling)

2. **Pre-Implementation**:
   - Create comprehensive TodoList using TodoWrite tool mapping all plan steps
   - Verify all dependencies are available: `uv sync`

3. **Implementation**:
   - Execute ONLY the modifications specified in the plan
   - Mark each step as in_progress/completed in TodoWrite as you work
   - Follow existing code conventions and patterns in the codebase
   - Add error handling and logging where specified in the plan
   - Use `uv run` for all Python executions

4. **Verification**:
   - Run tests after each major change: `uv run pytest [specific_test] -v -s`
   - Run full test suite: `make test-fast`
   - Run code quality checks: `make lint` and `make format`
   - Verify all plan requirements are met

5. **Documentation**:
   - Update the plan status to COMPLETED with implementation summary
   - Document any deviations or additional changes made
   - List all modified files with status indicators (✅/❌)
   - Move completed plan to `@_docs/plans/completed/` directory

### CONSTRAINTS:

- **STRICT SCOPE**: Only implement what's explicitly defined in the plan
- **NO FEATURE CREEP**: Do not add extra functionality beyond plan specifications  
- **TESTING REQUIRED**: All changes must pass existing tests
- **CODE QUALITY**: Must pass lint and format checks before completion

### POST-IMPLEMENTATION:

- Provide brief summary of what was implemented
- Suggest potential future enhancements (but don't implement them)
- Confirm all TodoWrite items are marked as completed
