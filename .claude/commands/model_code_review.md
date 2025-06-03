
## Overview

Conduct comprehensive code reviews using multiple AI models to get diverse perspectives on code changes. This workflow leverages the MCP code review tools to analyze git diffs across multiple LLM providers.

## Prerequisites

- Ensure your changes are staged: `git add <files>`
- Or have unstaged changes you want to review

## Workflow Steps

### Step 1: Run Multi-Model Code Review

Use the built-in MCP tools to analyze your code changes across multiple AI models:

**Option A: Review Git Diff (Recommended)**
```
Use the mcp__collect__run_git_diff_review tool with these parameters:
- staged_only: true (for staged changes only) or false (for all changes)  
- to_file: "codereview" (output directory name)
```

**Option B: Review Specific Diff File**
```
If you have a pre-made diff file, use mcp__collect__run_code_review with:
- from_file: "path/to/your/diff.md" 
- to_file: "codereview"
```

**Quick Start Commands:**
- For staged changes: Call `mcp__collect__run_git_diff_review` with `staged_only=true`
- For all changes: Call `mcp__collect__run_git_diff_review` with `staged_only=false`
- For file review: Call `mcp__collect__run_code_review` with your file path

### Step 2: Analyze Results

The tool automatically creates these files in the output directory (default: `codereview/`):
- `{model}_YYYYMMDD_HHMMSS.md` - Individual model reviews (e.g., `claude-3-5-sonnet-20241022_20241201_143052.md`)
- `errors_YYYYMMDD_HHMMSS.md` - Any failed model responses (if any models fail)
- `summary_YYYYMMDD_HHMMSS.json` - Review metadata and statistics

**Example output files:**
```
codereview/
├── claude-3-5-sonnet-20241022_20241201_143052.md
├── gpt-4-turbo-2024-04-09_20241201_143052.md  
├── gemini-2.0-flash-exp_20241201_143052.md
├── grok-beta_20241201_143052.md
├── summary_20241201_143052.json
└── errors_20241201_143052.md (if any failures)
```

### Step 3: Synthesize Findings

After the tool completes, review the individual model outputs and create a consolidated analysis:

1. **Read all model reviews** to identify common themes and unique insights
2. **Categorize findings** by severity and impact:
   - 🔴 Critical: Security, bugs, breaking changes
   - 🟡 Important: Performance, maintainability, best practices
   - 🟢 Minor: Style, documentation, optimizations
3. **Create action plan** with prioritized recommendations

### Step 4: Create Synthesis Report

Generate a comprehensive report in `codereview/synthesis_review.md`:

```markdown
# Multi-Model Code Review Synthesis

## Executive Summary
- Total models consulted: X
- Critical issues found: X
- Key recommendations: X

## Consensus Findings
[Issues identified by multiple models]

## Model-Specific Insights
[Unique perspectives from individual models]

## Priority Action Items
| Priority | Issue | Solution | Risk Level |
|----------|-------|----------|------------|
| 🔴 High | ... | ... | ... |
| 🟡 Medium | ... | ... | ... |
| 🟢 Low | ... | ... | ... |

## Implementation Recommendations
[Specific steps to address findings]
```

### Step 5: Review and Act

1. **Prioritize fixes** based on consensus and severity
2. **Implement changes** for high-priority items
3. **Re-run review** on critical fixes to validate improvements
4. **Document decisions** for future reference

## Advanced Usage

### Custom Prompts
The review prompt emphasizes:
- Security vulnerabilities and potential exploits
- Performance implications and bottlenecks
- Code maintainability and readability
- Best practices adherence
- Testing coverage and quality

### Model Coverage
Reviews typically include:
- **Anthropic Claude**: Strong reasoning and security analysis
- **OpenAI GPT**: Comprehensive code understanding
- **Google Gemini**: Multi-modal and pattern recognition
- **XAI Grok**: Alternative perspectives and edge cases

### Integration with Development Workflow
- Run before creating pull requests
- Use for pre-commit quality gates
- Integrate with CI/CD pipelines
- Archive reviews for historical analysis

## Practical Example

Here's a complete example workflow:

1. **Make some code changes and stage them:**
   ```bash
   git add src/components/UserAuth.tsx
   git add tests/auth.test.ts
   ```

2. **Run the code review:**
   Call the MCP tool `mcp__collect__run_git_diff_review` with:
   - `staged_only`: `true`
   - `to_file`: `"codereview"`

3. **Review the generated files:**
   ```bash
   ls codereview/
   # Shows: claude-3-5-sonnet-20241022_20241201_143052.md
   #        gpt-4-turbo-2024-04-09_20241201_143052.md
   #        gemini-2.0-flash-exp_20241201_143052.md
   #        summary_20241201_143052.json
   ```

4. **Read individual reviews** and look for common themes
5. **Create synthesis** in `codereview/synthesis_review.md`
6. **Implement fixes** based on consensus findings

## Tips for Best Results

1. **Stage meaningful chunks** - Review logical units of change
2. **Include context** - Add commit messages or PR descriptions
3. **Follow up on consensus** - Pay special attention to issues multiple models identify
4. **Balance perspectives** - Consider both conservative and innovative viewpoints
5. **Document decisions** - Track which recommendations you implement and why

## Troubleshooting

- **No git changes found**: Make sure you have staged changes (`git add`) or unstaged modifications
- **Tool fails**: Check the `errors_timestamp.md` file for specific model failures
- **Empty reviews**: Verify your diff contains meaningful code changes, not just whitespace
