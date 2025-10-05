# Directory Structure

```
/Users/benjaminmetz/python/collect-wt1
├── agents
│   └── tools.py
├── agentwork.py
├── api
│   ├── __init__.py
│   ├── prompt_api_models.py
│   └── prompt_api.py
├── api.py
├── CLAUDE_DRAFT.md
├── CLAUDE.md
├── collect.py
├── config.py
├── dir_structure.md
├── fetcher.py
├── filterModel.md
├── GEMINI.md
├── initial_load.py
├── llmrunner.py
├── Makefile
├── memory_map_files.md
├── migrations
│   ├── 20250727_01_create-prompt-tables.sql
│   ├── 20250810_01_add-projects-table.sql
│   └── 20250810_02_add-github-url-to-prompt-history.sql
├── models
│   ├── __init__.py
│   ├── anthropic_models.py
│   ├── anthropic_mpc.py
│   ├── anthropic_prompt_generate.py
│   ├── anthropic_prompt_improve.py
│   ├── anthropic_prompt_templatize.py
│   ├── gemini_mcp.py
│   ├── openai_mpc.py
│   ├── test_anthropic_mcp.py
│   ├── test_gemini_mcp.py
│   ├── test_openai_mcp.py
│   ├── test_xai_mcp.py
│   ├── test_youtube.py
│   ├── xai_mcp.py
│   ├── youtube_models.py
│   └── youtube.py
├── notebooks
│   ├── loader_testing.py
│   └── prompt_service_notebook.py
├── pyproject.toml
├── README.md
├── repository
│   ├── database.py
│   ├── datetime_adapters.py
│   ├── prompt_models.py
│   ├── prompt_service.py
│   ├── test_database.py
│   ├── test_datetime_adapters.py
│   └── test_prompt_service.py
├── requirements.txt
├── research
│   ├── DSPy-Beats-Human-Prompt-Engineering.md
│   ├── go_repo_crawler.md
│   ├── research_09_19.md
│   └── Sutskever's_List_v1_MEAP.pdf
├── reviewer
│   ├── __init__.py
│   ├── code_review.py
│   ├── live_test_codereview
│   │   ├── claude-opus-4-20250514_20250601_091219.md
│   │   ├── gemini-2.0-flash_20250601_091219.md
│   │   ├── grok-3-mini-fast-latest_20250601_091219.md
│   │   ├── o3-mini-2025-01-31_20250601_091219.md
│   │   └── summary_20250601_091219.json
│   ├── test_code_review_integration.py
│   ├── test_code_review_live.py
│   ├── test_code_review.py
│   ├── test_codereview
│   │   ├── errors_20250601_084601.md
│   │   ├── errors_20250601_084959.md
│   │   ├── summary_20250601_084601.json
│   │   └── summary_20250601_084959.json
│   ├── test_codereview_live
│   │   ├── errors_20250601_085957.md
│   │   └── summary_20250601_085957.json
│   └── test_diff.md
├── secret_manager.py
├── synctools
├── test_collect.py
├── test_generate_prompt.py
├── test_llmrunner.py
├── uv.lock
└── yoyo.ini

12 directories, 77 files
```
