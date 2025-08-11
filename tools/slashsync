#!/usr/bin/env python3
"""
GitHub Commands Sync and Conversion Script

This script uses GitHub CLI to fetch .claude/commands from the remote repository
and creates local .claude/commands and .gemini/commands directory structures.
It converts markdown command files to TOML format using Gemini 2.5 Pro.
"""

import asyncio
import json
import subprocess
import base64
import sys
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

try:
    import aiohttp
except ImportError:
    aiohttp = None

# No longer need project-specific dependencies - using gemini CLI directly


class Colors:
    """ANSI color codes for terminal output"""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colors
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"

    @classmethod
    def disable_colors(cls):
        """Disable colors for non-TTY environments"""
        for attr in dir(cls):
            if not attr.startswith("_") and attr != "disable_colors":
                setattr(cls, attr, "")


def show_help():
    """Display colorful and well-structured help information"""
    # Disable colors if not running in a TTY
    if not sys.stdout.isatty():
        Colors.disable_colors()

    help_text = f"""{Colors.BOLD}{Colors.BRIGHT_CYAN}
╭─────────────────────────────────────────────────────────────────────────────╮
│                     🚀 GitHub Commands Sync Tool                           │
╰─────────────────────────────────────────────────────────────────────────────╯{Colors.RESET}

{Colors.BRIGHT_YELLOW}DESCRIPTION:{Colors.RESET}
    {Colors.WHITE}Syncs {Colors.BRIGHT_BLUE}.claude/commands{Colors.WHITE} from GitHub and creates local directory
    structures with AI-powered markdown to TOML conversion using Gemini.{Colors.RESET}

{Colors.BRIGHT_YELLOW}USAGE:{Colors.RESET}
    {Colors.BRIGHT_GREEN}./sync_commands.py{Colors.RESET} {Colors.DIM}[OPTIONS]{Colors.RESET}
    {Colors.BRIGHT_GREEN}python sync_commands.py{Colors.RESET} {Colors.DIM}[OPTIONS]{Colors.RESET}

{Colors.BRIGHT_YELLOW}OPTIONS:{Colors.RESET}
    {Colors.BRIGHT_CYAN}--source-repo{Colors.RESET} {Colors.DIM}REPO{Colors.RESET}
        📂 Source GitHub repository
        {Colors.DIM}Default: austere-labs/collect{Colors.RESET}

    {Colors.BRIGHT_CYAN}--dry-run{Colors.RESET}
        🔍 Preview changes without making modifications
        {Colors.DIM}Shows what would be synced and converted{Colors.RESET}

    {Colors.BRIGHT_CYAN}--convert-only{Colors.RESET}
        🔄 Convert existing files without syncing from GitHub
        {Colors.DIM}Useful for re-converting local markdown files{Colors.RESET}

    {Colors.BRIGHT_CYAN}--help{Colors.RESET}, {Colors.BRIGHT_CYAN}-h{Colors.RESET}
        ❓ Show this help message

    {Colors.BRIGHT_CYAN}--version{Colors.RESET}, {Colors.BRIGHT_CYAN}-v{Colors.RESET}
        📋 Show version information

{Colors.BRIGHT_YELLOW}EXAMPLES:{Colors.RESET}
    {Colors.DIM}# Preview sync from default repository{Colors.RESET}
    {Colors.BRIGHT_GREEN}./sync_commands.py --dry-run{Colors.RESET}

    {Colors.DIM}# Sync from a different repository{Colors.RESET}
    {Colors.BRIGHT_GREEN}./sync_commands.py --source-repo myuser/myrepo{Colors.RESET}

    {Colors.DIM}# Convert existing local files only{Colors.RESET}
    {Colors.BRIGHT_GREEN}./sync_commands.py --convert-only{Colors.RESET}

{Colors.BRIGHT_YELLOW}WORKFLOW:{Colors.RESET}
    {Colors.BRIGHT_MAGENTA}1.{Colors.RESET} {Colors.WHITE}Fetches directory structure from GitHub{Colors.RESET}
    {Colors.BRIGHT_MAGENTA}2.{Colors.RESET} {Colors.WHITE}Creates local {Colors.BRIGHT_BLUE}.claude/commands{Colors.WHITE} and {Colors.BRIGHT_BLUE}.gemini/commands{Colors.WHITE} directories{Colors.RESET}
    {Colors.BRIGHT_MAGENTA}3.{Colors.RESET} {Colors.WHITE}Downloads markdown files to {Colors.BRIGHT_BLUE}.claude/commands{Colors.RESET}
    {Colors.BRIGHT_MAGENTA}4.{Colors.RESET} {Colors.WHITE}Converts markdown to TOML format using Gemini AI{Colors.RESET}
    {Colors.BRIGHT_MAGENTA}5.{Colors.RESET} {Colors.WHITE}Saves converted files to {Colors.BRIGHT_BLUE}.gemini/commands{Colors.RESET}

{Colors.BRIGHT_YELLOW}REQUIREMENTS:{Colors.RESET}
    {Colors.BRIGHT_RED}•{Colors.RESET} {Colors.WHITE}GitHub CLI ({Colors.BRIGHT_GREEN}gh{Colors.WHITE}) - for repository access{Colors.RESET}
    {Colors.BRIGHT_RED}•{Colors.RESET} {Colors.WHITE}Gemini CLI ({Colors.BRIGHT_GREEN}gemini{Colors.WHITE}) - for AI conversion{Colors.RESET}
    {Colors.BRIGHT_RED}•{Colors.RESET} {Colors.WHITE}Python 3.7+ with standard library{Colors.RESET}
    {Colors.BRIGHT_RED}•{Colors.RESET} {Colors.WHITE}aiohttp ({Colors.BRIGHT_GREEN}pip install aiohttp{Colors.WHITE}) - optional for faster concurrent downloads{Colors.RESET}

{Colors.DIM}For more information, visit: https://github.com/google-gemini/gemini-cli{Colors.RESET}
"""

    print(help_text)


def show_version():
    """Display version information"""
    if not sys.stdout.isatty():
        Colors.disable_colors()

    version_text = f"""{Colors.BOLD}{Colors.BRIGHT_CYAN}
╭─────────────────────────────────────────╮
│        🚀 GitHub Commands Sync         │
╰─────────────────────────────────────────╯{Colors.RESET}

{Colors.BRIGHT_YELLOW}Version:{Colors.RESET} {Colors.BRIGHT_GREEN}2.0.0{Colors.RESET}
{Colors.BRIGHT_YELLOW}Updated:{Colors.RESET} {Colors.WHITE}2025-01-10{Colors.RESET}
{Colors.BRIGHT_YELLOW}Author:{Colors.RESET}  {Colors.WHITE}Austere Labs{Colors.RESET}

{Colors.DIM}Powered by Gemini AI for intelligent markdown to TOML conversion{Colors.RESET}
"""
    print(version_text)


@dataclass
class FileInfo:
    """Information about a file from GitHub API"""

    name: str
    path: str
    download_url: str
    sha: str = ""
    content: str = ""


@dataclass
class CacheEntry:
    """Cache entry for file metadata"""
    
    sha: str
    path: str
    last_synced: float
    converted: bool = False
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CacheEntry':
        return cls(**data)
    
    def to_dict(self) -> dict:
        return asdict(self)


class GitHubCommandsSyncer:
    """Handles syncing and converting commands from GitHub using GitHub CLI"""

    def __init__(self, source_repo: str = "austere-labs/collect"):
        self.source_repo = source_repo
        self.cache_file = Path(".sync_cache.json")
        self.cache: Dict[str, CacheEntry] = {}
        self._load_cache()
        # Semaphore to limit concurrent operations
        self.gemini_semaphore = asyncio.Semaphore(3)  # Limit Gemini calls
        self.github_semaphore = asyncio.Semaphore(10)  # Limit GitHub API calls

    def _load_cache(self):
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    self.cache = {
                        path: CacheEntry.from_dict(entry) 
                        for path, entry in cache_data.items()
                    }
            except Exception as e:
                print(f"Warning: Could not load cache: {e}")
                self.cache = {}

    def _save_cache(self):
        """Save cache to disk"""
        try:
            cache_data = {
                path: entry.to_dict() 
                for path, entry in self.cache.items()
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")

    async def _run_gh_command_async(self, args: List[str]) -> Tuple[str, int]:
        """Run a GitHub CLI command asynchronously and return output and return code"""
        async with self.github_semaphore:
            try:
                process = await asyncio.create_subprocess_exec(
                    "gh", *args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                return stdout.decode().strip(), process.returncode
            except Exception as e:
                raise RuntimeError(f"GitHub CLI command failed: {e}")

    def _run_gh_command(self, args: List[str]) -> Tuple[str, int]:
        """Run a GitHub CLI command and return output and return code"""
        try:
            result = subprocess.run(
                ["gh"] + args, capture_output=True, text=True, check=False
            )
            return result.stdout.strip(), result.returncode
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"GitHub CLI command failed: {e}")

    async def _run_gemini_command_async(self, prompt: str, model: str = "gemini-2.5-flash") -> str:
        """Run a gemini CLI command asynchronously and return the response"""
        async with self.gemini_semaphore:
            try:
                process = await asyncio.create_subprocess_exec(
                    "gemini", "-p", prompt, "--model", model,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    raise RuntimeError(f"Gemini CLI command failed: {stderr.decode()}")

                return stdout.decode().strip()
            except Exception as e:
                raise RuntimeError(f"Gemini CLI command failed: {e}")

    def _run_gemini_command(self, prompt: str, model: str = "gemini-2.5-flash") -> str:
        """Run a gemini CLI command and return the response"""
        try:
            # Use gemini CLI with non-interactive prompt mode
            result = subprocess.run(
                ["gemini", "-p", prompt, "--model", model],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Gemini CLI command failed: {result.stderr}")

            return result.stdout.strip()
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Gemini CLI command failed: {e}")
        except FileNotFoundError:
            raise RuntimeError(
                "Gemini CLI not found. Please install it with: brew install gemini-cli"
            )

    async def fetch_all_files_optimized(self, base_path: str = ".claude/commands") -> List[FileInfo]:
        """Optimized method to fetch all markdown files using single recursive tree API call"""
        args = ["api", f"repos/{self.source_repo}/git/trees/HEAD?recursive=1"]
        output, returncode = await self._run_gh_command_async(args)

        if returncode != 0:
            raise RuntimeError(f"Failed to get recursive tree: {output}")

        try:
            data = json.loads(output)
            files = []

            for item in data.get("tree", []):
                if (
                    item["type"] == "blob"
                    and item["path"].startswith(base_path)
                    and item["path"].endswith(".md")
                ):
                    files.append(FileInfo(
                        name=Path(item["path"]).name,
                        path=item["path"],
                        download_url=f"https://raw.githubusercontent.com/{self.source_repo}/HEAD/{item['path']}",
                        sha=item["sha"]
                    ))

            return files
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from GitHub API: {e}")

    async def get_directories_from_files(self, files: List[FileInfo]) -> List[str]:
        """Extract unique directories from file paths"""
        directories = set()
        for file_info in files:
            dir_path = str(Path(file_info.path).parent)
            if dir_path != ".claude/commands":
                directories.add(dir_path)
        return list(directories)

    async def download_file_content_async(self, file_info: FileInfo) -> str:
        """Download file content using aiohttp if available, fallback to gh CLI"""
        # Check cache first
        cached_entry = self.cache.get(file_info.path)
        if cached_entry and cached_entry.sha == file_info.sha:
            print(f"  → Cache hit for {file_info.path}")
            # Read from local file if it exists
            local_path = Path(file_info.path)
            if local_path.exists():
                return local_path.read_text(encoding="utf-8")

        if aiohttp and file_info.download_url:
            try:
                return await self._download_with_aiohttp(file_info)
            except Exception as e:
                print(f"  → aiohttp failed for {file_info.path}, falling back to gh CLI: {e}")

        # Fallback to GitHub CLI
        return await self._download_with_gh_cli(file_info.path)

    async def _download_with_aiohttp(self, file_info: FileInfo) -> str:
        """Download file using aiohttp for better performance"""
        async with self.github_semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.get(file_info.download_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Update cache
                        self.cache[file_info.path] = CacheEntry(
                            sha=file_info.sha,
                            path=file_info.path,
                            last_synced=time.time()
                        )
                        return content
                    else:
                        raise RuntimeError(f"HTTP {response.status}: {await response.text()}")

    async def _download_with_gh_cli(self, file_path: str) -> str:
        """Download file using GitHub CLI as fallback"""
        args = ["api", f"repos/{self.source_repo}/contents/{file_path}"]
        output, returncode = await self._run_gh_command_async(args)

        if returncode != 0:
            raise RuntimeError(f"Failed to download file {file_path}: {output}")

        try:
            data = json.loads(output)
            if data.get("encoding") == "base64":
                content = base64.b64decode(data["content"]).decode("utf-8")
                # Update cache
                self.cache[file_path] = CacheEntry(
                    sha=data.get("sha", ""),
                    path=file_path,
                    last_synced=time.time()
                )
                return content
            else:
                raise ValueError(f"Unexpected encoding: {data.get('encoding')}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from GitHub API: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to decode file content: {e}")

    # Keep old methods for backwards compatibility
    def fetch_directory_tree(self, path: str = ".claude/commands") -> List[Dict]:
        """Use GitHub CLI to get directory structure"""
        args = ["api", f"repos/{self.source_repo}/contents/{path}"]
        output, returncode = self._run_gh_command(args)

        if returncode != 0:
            raise RuntimeError(f"Failed to fetch directory tree: {output}")

        try:
            return json.loads(output)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from GitHub API: {e}")

    def download_file_content(self, file_path: str) -> str:
        """Download individual file content using GitHub CLI"""
        args = ["api", f"repos/{self.source_repo}/contents/{file_path}"]
        output, returncode = self._run_gh_command(args)

        if returncode != 0:
            raise RuntimeError(f"Failed to download file {file_path}: {output}")

        try:
            data = json.loads(output)
            if data.get("encoding") == "base64":
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
            else:
                raise ValueError(f"Unexpected encoding: {data.get('encoding')}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from GitHub API: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to decode file content: {e}")

    def create_local_directories(
        self, directories: List[str], dry_run: bool = False
    ) -> None:
        """Create local directory structure mirroring remote"""
        base_dirs = [".claude/commands", ".gemini/commands"]

        for base_dir in base_dirs:
            if not dry_run:
                Path(base_dir).mkdir(parents=True, exist_ok=True)
                print(f"Created base directory: {base_dir}")
            else:
                print(f"Would create base directory: {base_dir}")

        for remote_dir in directories:
            # Convert .claude/commands path to local equivalents
            if remote_dir.startswith(".claude/commands/"):
                local_claude = remote_dir
                local_gemini = remote_dir.replace(
                    ".claude/commands/", ".gemini/commands/"
                )

                for local_dir in [local_claude, local_gemini]:
                    if not dry_run:
                        Path(local_dir).mkdir(parents=True, exist_ok=True)
                        print(f"Created directory: {local_dir}")
                    else:
                        print(f"Would create directory: {local_dir}")

    async def convert_markdown_to_toml_async(self, markdown_content: str, file_path: str) -> str:
        """Convert markdown command to TOML format using Gemini CLI asynchronously"""
        # Check if already converted in cache
        cached_entry = self.cache.get(file_path)
        if cached_entry and cached_entry.converted:
            gemini_path = Path(file_path.replace(".claude/commands/", ".gemini/commands/")).with_suffix(".toml")
            if gemini_path.exists():
                print(f"  → Using cached conversion for {file_path}")
                return gemini_path.read_text(encoding="utf-8")

        conversion_prompt = f"""Convert the following markdown command to TOML format while preserving all semantic meaning and functionality:

{markdown_content}

Output should be valid TOML with appropriate sections and key-value pairs that represent the same information structure as the original markdown. Focus on maintaining the command structure, parameters, descriptions, and any metadata present in the markdown format. Only output the TOML content, no explanations."""

        try:
            result = await self._run_gemini_command_async(conversion_prompt, "gemini-2.5-flash")
            # Update cache to mark as converted
            if file_path in self.cache:
                self.cache[file_path].converted = True
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to convert markdown to TOML: {e}")

    def convert_markdown_to_toml(self, markdown_content: str) -> str:
        """Convert markdown command to TOML format using Gemini CLI"""
        conversion_prompt = f"""Convert the following markdown command to TOML format while preserving all semantic meaning and functionality:

{markdown_content}

Output should be valid TOML with appropriate sections and key-value pairs that represent the same information structure as the original markdown. Focus on maintaining the command structure, parameters, descriptions, and any metadata present in the markdown format. Only output the TOML content, no explanations."""

        try:
            return self._run_gemini_command(conversion_prompt, "gemini-2.5-flash")
        except Exception as e:
            raise RuntimeError(f"Failed to convert markdown to TOML: {e}")

    def get_all_markdown_files(
        self, base_path: str = ".claude/commands"
    ) -> List[FileInfo]:
        """Get all markdown files from the repository"""
        all_files = []

        # Get files from base directory
        try:
            contents = self.fetch_directory_tree(base_path)
            for item in contents:
                if item["type"] == "file" and item["name"].endswith(".md"):
                    file_info = FileInfo(
                        name=item["name"],
                        path=item["path"],
                        download_url=item.get("download_url", ""),
                    )
                    all_files.append(file_info)
        except Exception as e:
            print(f"Warning: Could not fetch files from {base_path}: {e}")

        # Get files from subdirectories
        try:
            subdirectories = self.list_subdirectories(base_path)
            for subdir in subdirectories:
                try:
                    contents = self.fetch_directory_tree(subdir)
                    for item in contents:
                        if item["type"] == "file" and item["name"].endswith(".md"):
                            file_info = FileInfo(
                                name=item["name"],
                                path=item["path"],
                                download_url=item.get("download_url", ""),
                            )
                            all_files.append(file_info)
                except Exception as e:
                    print(f"Warning: Could not fetch files from {subdir}: {e}")
        except Exception as e:
            print(f"Warning: Could not list subdirectories: {e}")

        return all_files

    async def sync_and_convert_commands_optimized(
        self, dry_run: bool = False, convert_only: bool = False
    ) -> Dict[str, int]:
        """Optimized main orchestration function with concurrent processing"""
        results = {"synced": 0, "converted": 0, "errors": 0, "cached": 0}
        start_time = time.time()

        try:
            print(f"🚀 Starting optimized sync from {self.source_repo}")
            
            if aiohttp:
                print("✅ Using aiohttp for concurrent downloads")
            else:
                print("⚠️  aiohttp not available, install with: pip install aiohttp")

            # Get all markdown files using optimized single API call
            print("📁 Fetching file tree...")
            markdown_files = await self.fetch_all_files_optimized()
            print(f"📄 Found {len(markdown_files)} markdown files")

            # Get directories from file paths and create local structure
            if not convert_only:
                directories = await self.get_directories_from_files(markdown_files)
                print(f"📂 Creating {len(directories)} directories...")
                self.create_local_directories(directories, dry_run)

            # Process files concurrently
            semaphore = asyncio.Semaphore(8)  # Limit concurrent file processing
            tasks = []
            
            for file_info in markdown_files:
                task = self._process_single_file_async(
                    file_info, semaphore, dry_run, results
                )
                tasks.append(task)

            # Execute all tasks concurrently with progress tracking
            print(f"⚡ Processing {len(tasks)} files concurrently...")
            await asyncio.gather(*tasks, return_exceptions=True)

            # Save cache
            self._save_cache()
            
            elapsed = time.time() - start_time
            print(f"\n✅ Completed in {elapsed:.1f}s: {results['synced']} synced, "
                  f"{results['converted']} converted, {results['cached']} cached, "
                  f"{results['errors']} errors")
            
            return results

        except Exception as e:
            print(f"💥 Fatal error during sync: {e}")
            results["errors"] += 1
            return results

    async def _process_single_file_async(
        self, file_info: FileInfo, semaphore: asyncio.Semaphore, 
        dry_run: bool, results: Dict[str, int]
    ):
        """Process a single file with error handling"""
        async with semaphore:
            try:
                print(f"🔄 Processing {file_info.path}")

                # Download content (with caching)
                file_info.content = await self.download_file_content_async(file_info)
                
                # Check if this was a cache hit
                cached_entry = self.cache.get(file_info.path)
                if cached_entry and cached_entry.sha == file_info.sha:
                    results["cached"] += 1

                # Write to .claude/commands
                local_claude_path = Path(file_info.path)
                if not dry_run:
                    local_claude_path.parent.mkdir(parents=True, exist_ok=True)
                    local_claude_path.write_text(file_info.content, encoding="utf-8")
                    results["synced"] += 1
                    print(f"  ✅ Synced to {local_claude_path}")
                else:
                    print(f"  🔍 Would sync to {local_claude_path}")

                # Convert and write to .gemini/commands concurrently
                gemini_path = Path(
                    file_info.path.replace(".claude/commands/", ".gemini/commands/")
                ).with_suffix(".toml")

                if not dry_run:
                    converted_content = await self.convert_markdown_to_toml_async(
                        file_info.content, file_info.path
                    )
                    gemini_path.parent.mkdir(parents=True, exist_ok=True)
                    gemini_path.write_text(converted_content, encoding="utf-8")
                    results["converted"] += 1
                    print(f"  🔄 Converted to {gemini_path}")
                else:
                    print(f"  🔍 Would convert to {gemini_path}")

            except Exception as e:
                print(f"  ❌ Error processing {file_info.path}: {e}")
                results["errors"] += 1

    # Keep old method for backwards compatibility
    async def sync_and_convert_commands(
        self, dry_run: bool = False, convert_only: bool = False
    ) -> Dict[str, int]:
        """Main orchestration function to sync and convert commands"""
        # Use optimized version
        return await self.sync_and_convert_commands_optimized(dry_run, convert_only)


async def main():
    """Entry point for script execution"""
    import argparse

    # Handle help and version before argparse to show custom formatted output
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h", "help"]:
            show_help()
            sys.exit(0)
        elif sys.argv[1] in ["--version", "-v", "version"]:
            show_version()
            sys.exit(0)

    parser = argparse.ArgumentParser(
        description="🚀 Sync and convert GitHub commands with AI-powered conversion",
        add_help=False,  # Disable default help to use custom
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--source-repo",
        default="austere-labs/collect",
        help="📂 Source repository (default: austere-labs/collect)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="🔍 Preview changes without making modifications",
    )
    parser.add_argument(
        "--convert-only",
        action="store_true",
        help="🔄 Convert existing files without syncing from GitHub",
    )
    parser.add_argument(
        "--help", "-h", action="store_true", help="❓ Show detailed help information"
    )
    parser.add_argument(
        "--version", "-v", action="store_true", help="📋 Show version information"
    )

    try:
        args = parser.parse_args()
    except SystemExit:
        # If argparse fails, show our custom help
        show_help()
        sys.exit(1)

    # Handle help and version flags
    if getattr(args, "help", False):
        show_help()
        return

    if getattr(args, "version", False):
        show_version()
        return

    syncer = GitHubCommandsSyncer(args.source_repo)
    results = await syncer.sync_and_convert_commands(
        dry_run=args.dry_run, convert_only=args.convert_only
    )

    return results


if __name__ == "__main__":
    asyncio.run(main())
