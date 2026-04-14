---
description: "Creates comprehensive progress reports tracking session work, technical changes, issues, and context for continuity across Claude Code sessions"
model: claude-opus-4-20250514
argument-hint: "[filename]"
allowed-tools: Read, Write, Bash, TodoWrite, Glob, Grep
---

# Progress Documentation Command

Write a comprehensive progress report to `_progress/{{filename}}` (default: `_progress/Progress.md`). Create the `_progress` directory if it doesn't exist.

## What to Include:

### Session Overview
- **Current Task/Goal**: What we're working on right now
- **Session Start Context**: Brief summary of where we began
- **Overall Progress**: High-level status and completion percentage

### Approach & Strategy
- **Method**: The approach we're taking to solve the problem
- **Architecture Decisions**: Key technical decisions made
- **Tools & Technologies**: What we're using and why

### Detailed Progress
- **Completed Steps**: What we've successfully accomplished (with timestamps if relevant)
- **Current Work**: What we're actively working on
- **Pending Tasks**: What's queued up next
- **Todo List Status**: Current state of any active todo lists

### Technical Details
- **Files Modified**: List of files we've changed with brief description of changes
- **Code Changes**: Key functions, classes, or components added/modified
- **Database Changes**: Schema updates, migrations, data changes
- **Configuration Updates**: Environment, dependencies, or settings changes

### Issues & Blockers
- **Current Failures**: Any failing tests, build errors, or broken functionality
- **Blockers**: What's preventing progress
- **Workarounds**: Temporary solutions in place
- **Debugging Notes**: Important findings from troubleshooting

### Testing & Validation
- **Tests Run**: What we've tested and results
- **Manual Testing**: User flows or features we've verified
- **Performance**: Any performance metrics or observations
- **Quality Checks**: Linting, type checking, code review status

### Next Steps
- **Immediate Actions**: What needs to happen next
- **Risk Assessment**: Potential issues to watch for
- **Success Criteria**: How we'll know when we're done

### Context for Future Sessions
- **Key Insights**: Important discoveries or learnings
- **Gotchas**: Things to remember or be careful about
- **Useful Commands**: Commands that were helpful during this session
- **References**: Important documentation, URLs, or resources used

Format the report in clear markdown with proper headings, bullet points, and code blocks where appropriate. Include enough detail that someone (or future Claude sessions) can understand the current state and continue the work effectively.

Usage: `/progress [filename]`
Example: `/progress Sprint1_Progress.md` (saves to `_progress/Sprint1_Progress.md`)
