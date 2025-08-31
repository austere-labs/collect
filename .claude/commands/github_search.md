---
argument-hint: [filename] [optional: --repo owner/repo] [optional: --language lang]
description: Search GitHub for files by name, then download or read selected files
---

## GitHub File Search Tool

Search for files on GitHub using the filename provided and allow the user to:
1. View search results with numbered options
2. Select a file to either download locally or read/display content

### Instructions:

You will receive a filename and optional parameters. Follow these steps:

#### 1. Parse Arguments
- Extract the filename from the first argument
- Check for optional `--repo owner/repo` flag to limit search to specific repository  
- Check for optional `--language lang` flag to filter by programming language
- Check for optional `--limit N` to override default result limit (default: 10)

#### 2. Execute GitHub Search
Use the GitHub CLI to search for files:
```bash
gh search code --filename "{filename}" --limit 10 --json path,repository,url,sha
```

Add additional flags if provided:
- If `--repo` specified: add `--repo {owner/repo}`
- If `--language` specified: add `--language {language}`
- If `--limit` specified: use that number instead of 10

#### 3. Display Search Results
Parse the JSON output and display results in this format:
```
Found {N} files matching "{filename}":

[1] {filename} 
    Repository: {owner/repo}
    Path: {full_path}
    URL: {github_url}

[2] {filename}
    Repository: {owner/repo} 
    Path: {full_path}
    URL: {github_url}

...
```

#### 4. Get User Selection
Ask the user: 
"Select a file by number (1-{N}), or type 'q' to quit:"

Wait for user input.

#### 5. Execute User Choice
Once user selects a number:

Ask: "Would you like to (d)ownload or (r)ead this file? [d/r]:"

**For Download (d):**
- Get file content using: `gh api repos/{owner}/{repo}/contents/{path} --jq -r '.download_url' | xargs curl -s -o {filename}`
- Save to current directory with original filename
- Confirm: "Downloaded {filename} to current directory"

**For Read (r):**
- Get and display file content using: `gh api repos/{owner}/{repo}/contents/{path} --jq -r '.download_url' | xargs curl -s`
- Display the content with syntax highlighting if possible
- Show first 50 lines, then ask if user wants to see more for large files

#### 6. Handle Edge Cases
- **No results found**: Display "No files found matching '{filename}'"
- **Invalid selection**: Ask user to try again
- **API rate limit**: Display helpful error message
- **Authentication required**: Prompt user to run `gh auth login`
- **Large files**: Warn before displaying large files and offer download instead

#### 7. Additional Features
- Support searching within file content by using the filename as a content search term
- Allow multiple file downloads by accepting comma-separated numbers
- Show file size when available in API response
- Handle binary files appropriately (offer download only)

### Error Handling
- Validate GitHub CLI is installed and authenticated
- Handle network connectivity issues gracefully
- Provide clear error messages for common issues
- Offer suggestions for refining search if no results found

### Example Usage Patterns
- `github_search package.json` - Find all package.json files
- `github_search README.md --language javascript` - Find README files in JS repos
- `github_search config.yml --repo microsoft/vscode` - Search specific repository
- `github_search database.py --limit 5` - Limit results to 5 files

Process the filename: {filename}
