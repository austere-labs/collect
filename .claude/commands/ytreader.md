---
allowed-tools: Bash(uv:*)
description: Analyze YouTube video content using Gemini API and create a summary
argument-hint: [youtube_url] [filename]
---

Analyze the YouTube video and save the summary to `research/youtube_summaries/` directory.

## Instructions:
1. Extract the YouTube URL from the arguments (required)
2. Extract the filename from the arguments (optional - defaults to timestamped file if not provided)
3. Prepend `research/youtube_summaries/` to the filename
4. Run the ytreader.py script with the full path

## Command:
```bash
uv run ytreader.py "{youtube_url}" research/youtube_summaries/{filename}
```

## Examples:
- With filename: `uv run ytreader.py "https://youtube.com/watch?v=abc123" research/youtube_summaries/video_summary.md`
- Auto-generated filename: `uv run ytreader.py "https://youtube.com/watch?v=abc123" research/youtube_summaries/youtube_analysis_TIMESTAMP.md`

## Notes:
- All summaries are saved to `research/youtube_summaries/` directory
- Directory will be created automatically if it doesn't exist
- If no filename is provided, generates timestamped filename in the target directory
- Summary will be written in markdown format
