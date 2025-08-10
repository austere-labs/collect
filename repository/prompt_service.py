import sqlite3
from pathlib import Path
import uuid
import json
from datetime import datetime, timezone
import hashlib
from typing import Optional, List, Tuple
from repository.prompt_models import (
    PromptLoadResult,
    LoadError,
    CmdCategory,
    PromptType,
    PromptPlanStatus,
    PromptData,
    Prompt,
    PromptCreateResult,
    PromptDeleteResult,
    PromptFlattenResult,
)
from config import Config


class PromptService:
    def __init__(self, conn: sqlite3.Connection, config: Config):
        self.conn = conn
        self.config = config
        self.plans_check_dirs()
        self.cmd_check_dirs()

    def plans_check_dirs(self) -> bool:
        """Check if all required plan directories exist, create them if missing

        Returns:
            bool: True if all directories exist or were created successfully,
            False on error
        """
        project_dir = Path(__file__).parent.parent
        plans_dir = project_dir / "_docs" / "plans"

        # Required directories
        required_dirs = [
            plans_dir,
            plans_dir / "drafts",
            plans_dir / "approved",
            plans_dir / "completed",
        ]

        missing_dirs = []
        created_dirs = []

        for dir_path in required_dirs:
            if not dir_path.exists():
                missing_dirs.append(dir_path)

        if missing_dirs:
            print("📁 Creating missing plan directories:")
            for missing_dir in missing_dirs:
                try:
                    missing_dir.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(missing_dir)
                    print(
                        f"   ✅ Created: {
                            missing_dir.relative_to(project_dir)}"
                    )
                except Exception as e:
                    print(
                        f"   ❌ Failed to create {
                            missing_dir.relative_to(project_dir)}: {e}"
                    )
                    return False

            if created_dirs:
                print(
                    f"📁 Successfully created {
                        len(created_dirs)} directories"
                )
        else:
            print("✅ All required plan directories exist")

        return True

    def cmd_check_dirs(self) -> bool:
        """Check if all required command directories exist,
           create them if missing

        Returns:
            bool: True if all directories exist or were created successfully,
            False on error
        """
        project_dir = Path(__file__).parent.parent
        claude_dir = project_dir / ".claude"
        gemini_dir = project_dir / ".gemini"

        # Get subdirectories from config
        config = Config()
        subdirs = config.command_subdirs

        # Build required directories
        required_dirs = {
            "claude": [claude_dir / "commands"]
            + [claude_dir / "commands" / subdir for subdir in subdirs],
            "gemini": [gemini_dir / "commands"]
            + [gemini_dir / "commands" / subdir for subdir in subdirs],
        }

        # Check for missing directories by type
        missing_by_type = {"claude": [], "gemini": []}
        for dir_type, dirs in required_dirs.items():
            for dir_path in dirs:
                if not dir_path.exists():
                    missing_by_type[dir_type].append(dir_path)

        # Count total missing
        total_missing = sum(len(dirs) for dirs in missing_by_type.values())

        if total_missing == 0:
            print("✅ All required command directories exist")
            return True

        # Create missing directories
        print(f"📁 Creating {total_missing} missing command directories:")
        created_count = 0
        failed = False

        for dir_type, missing_dirs in missing_by_type.items():
            if missing_dirs:
                print(f"\n   {dir_type.title()} directories:")
                for missing_dir in missing_dirs:
                    try:
                        missing_dir.mkdir(parents=True, exist_ok=True)
                        created_count += 1
                        print(
                            f"   ✅ Created: {
                                missing_dir.relative_to(project_dir)}"
                        )
                    except Exception as e:
                        print(
                            f"   ❌ Failed to create {
                                missing_dir.relative_to(project_dir)}: {e}"
                        )
                        failed = True

        if created_count > 0:
            print(f"\n📁 Successfully created {created_count} directories")

        return not failed

    def _load_cmds_from_directory(
        self, cmds_dir: Path, source: str
    ) -> Tuple[List[Prompt], List[LoadError]]:
        """Load commands from a specific directory

        Args:
            cmds_dir: Path to the commands directory
            source: Source identifier ('claude' or 'gemini')

        Returns:
            Tuple of (prompts list, errors list)
        """
        prompts = []
        errors = []

        if not cmds_dir.exists():
            return prompts, errors

        # Loop through the files in cmds dir and load prompts first
        for file in cmds_dir.iterdir():
            if file.is_file():
                try:
                    # Check if filename adheres to naming rules
                    current_filename = file.name
                    if not self.check_filename(current_filename):
                        # Only rename files during explicit operations, not during loading
                        # Skip file renaming when just loading/reading files
                        print(
                            f"⚠️  File {
                                current_filename} doesn't follow naming convention but will not be renamed during load operation"
                        )

                    prompt_content = file.read_text()
                    prompt = self.new_prompt_model(
                        prompt_content=prompt_content,
                        name=file.name,
                        prompt_type=PromptType.CMD,
                        cmd_category=CmdCategory.UNCATEGORIZED,
                        status=PromptPlanStatus.DRAFT,
                        tags=[source],  # Add source tag
                    )
                    prompts.append(prompt)

                except Exception as e:
                    errors.append(
                        LoadError(
                            filename=str(file),
                            error_message=str(e),
                            error_type=type(e).__name__,
                        )
                    )

        # Then cycle through the subdirs, create Prompt models and append
        for sub_dir in cmds_dir.iterdir():
            if sub_dir.is_dir():
                try:
                    cmd_category = CmdCategory(sub_dir.name.lower())

                    for file in sub_dir.iterdir():
                        try:
                            if file.is_file():
                                # Check if filename adheres to naming rules
                                current_filename = file.name
                                if not self.check_filename(current_filename):
                                    # Normalize the filename
                                    fixed_filename = self.normalize_filename(
                                        current_filename
                                    )

                                    # Create new file path with normalized name
                                    new_file_path = file.parent / fixed_filename

                                    # Rename the file on disk
                                    file.rename(new_file_path)

                                    # Update file reference to the new path
                                    file = new_file_path
                                    print(
                                        f"📝 Renamed: {current_filename} → {
                                            fixed_filename}"
                                    )

                                prompt_content = file.read_text()
                                prompt = self.new_prompt_model(
                                    prompt_content=prompt_content,
                                    name=file.name,
                                    prompt_type=PromptType.CMD,
                                    cmd_category=cmd_category,
                                    status=PromptPlanStatus.DRAFT,
                                    tags=[source],  # Add source tag
                                )
                                prompts.append(prompt)

                        except Exception as e:
                            errors.append(
                                LoadError(
                                    filename=str(file),
                                    error_message=str(e),
                                    error_type=type(e).__name__,
                                )
                            )
                except ValueError:
                    # Skip directories that don't match valid CmdCategory values
                    continue

        return prompts, errors

    def load_cmds_from_disk(self) -> PromptLoadResult:
        """Load commands from both .claude and .gemini directories

        Returns:
            PromptLoadResult: Combined results from both directories
        """
        project_dir = Path(__file__).parent.parent
        claude_cmds_dir = project_dir / ".claude" / "commands"
        gemini_cmds_dir = project_dir / ".gemini" / "commands"

        all_prompts = []
        all_errors = []

        # Load from Claude directory
        claude_prompts, claude_errors = self._load_cmds_from_directory(
            claude_cmds_dir, "claude"
        )
        all_prompts.extend(claude_prompts)
        all_errors.extend(claude_errors)

        # Load from Gemini directory
        gemini_prompts, gemini_errors = self._load_cmds_from_directory(
            gemini_cmds_dir, "gemini"
        )
        all_prompts.extend(gemini_prompts)
        all_errors.extend(gemini_errors)

        return PromptLoadResult(
            loaded_prompts=all_prompts,
            errors=all_errors,
        )

    def load_plans_from_disk(self) -> PromptLoadResult:
        project_dir = Path(__file__).parent.parent
        plans_dir = project_dir / "_docs" / "plans"

        status_mapping = {
            "drafts": PromptPlanStatus.DRAFT,
            "approved": PromptPlanStatus.APPROVED,
            "completed": PromptPlanStatus.COMPLETED,
        }

        prompts = []
        errors = []

        for subdir in plans_dir.iterdir():
            if subdir.is_dir() and subdir.name in status_mapping:
                cmd_category = None
                status = status_mapping[subdir.name]
                for file in subdir.iterdir():
                    try:
                        if file.is_file():
                            # Check if filename adheres to naming rules
                            current_filename = file.name
                            if not self.check_filename(current_filename):
                                # Normalize the filename
                                fixed_filename = self.normalize_filename(
                                    current_filename
                                )

                                # Create new file path with normalized name
                                new_file_path = file.parent / fixed_filename

                                # Rename the file on disk
                                file.rename(new_file_path)

                                # Update file reference to the new path
                                file = new_file_path
                                print(
                                    f"""📝 Renamed: {current_filename} → {
                                        fixed_filename}
                                      """
                                )

                            prompts.append(
                                self.new_prompt_model(
                                    prompt_content=file.read_text(),
                                    name=file.name,
                                    prompt_type=PromptType.PLAN,
                                    github_url=self.config.github_url,
                                    cmd_category=cmd_category,
                                    status=status,
                                    project=project_dir.name,
                                )
                            )

                    except Exception as e:
                        errors.append(
                            LoadError(
                                filename=str(file),
                                error_message=str(e),
                                error_type=type(e).__name__,
                            )
                        )

        return PromptLoadResult(loaded_prompts=prompts, errors=errors)

    def normalize_filename(self, filename: str) -> str:
        """Normalize filename to use underscores and ensure .md or .toml extension

        Args:
            filename: The original filename

        Returns:
            Normalized filename with underscores and .md or .toml extension
        """
        # Replace hyphens with underscores
        normalized = filename.replace("-", "_")

        # Check if it already has .md or .toml extension
        if normalized.endswith(".md") or normalized.endswith(".toml"):
            return normalized

        # If it has another extension, replace it with .md
        if "." in normalized:
            normalized = normalized.rsplit(".", 1)[0] + ".md"
        else:
            # No extension, add .md as default
            normalized = normalized + ".md"

        return normalized

    def check_filename(self, filename: str) -> bool:
        """Check if filename adheres to naming rules
        (underscores and .md or .toml extension)

        Args:
            filename: The filename to check

        Returns:
            bool: True if filename follows the rules, False otherwise
        """
        # Check if filename has .md or .toml extension
        if not (filename.endswith(".md") or filename.endswith(".toml")):
            return False

        # Check if filename contains hyphens (should use underscores)
        if "-" in filename:
            return False

        return True

    def new_prompt_model(
        self,
        prompt_content: str,
        name: str,
        prompt_type: PromptType,
        github_url: Optional[str] = None,
        cmd_category: Optional[CmdCategory] = None,
        status: PromptPlanStatus = PromptPlanStatus.DRAFT,
        project: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Prompt:
        if prompt_type == PromptType.CMD and not cmd_category:
            raise ValueError("CMD type prompts require a category")

        default_tags = []
        if cmd_category:
            # Handle both enum and string values
            if isinstance(cmd_category, str):
                default_tags.append(cmd_category)
            else:
                default_tags.append(cmd_category.value)
        default_tags.append(prompt_type.value)

        # Merge custom tags with default tags
        all_tags = default_tags + (tags if tags else [])

        prompt_data = PromptData(
            type=prompt_type,
            status=status,
            project=project,
            cmd_category=cmd_category,
            content=prompt_content,
            description=description,
            tags=all_tags,
        )

        content_hash = hashlib.sha256(prompt_content.encode("utf-8")).hexdigest()

        timestamp = datetime.now(timezone.utc)

        db_name = self.create_db_name(
            prompt_type=prompt_type,
            prompt_status=status,
            cmd_category=cmd_category,
            project_name=project,
            name=name,
        )

        prompt = Prompt(
            id=str(uuid.uuid4()),
            name=db_name,
            github_url=github_url,
            data=prompt_data,
            version=1,
            content_hash=content_hash,
            created_at=timestamp,
            updated_at=timestamp,
        )

        return prompt

    def create_db_name(
        self,
        prompt_type: PromptType,
        prompt_status: Optional[PromptPlanStatus],
        cmd_category: Optional[CmdCategory],
        project_name: Optional[str],
        name: str,
    ) -> str:
        # in the directory [project]/_docs/plans:
        # there are directories: draft, approved and completed
        # we model those as PromptPlanStatus -> see prompt_models.py
        if prompt_type == PromptType.PLAN:
            create_name = project_name + "_" + prompt_status.value + "_" + name
        if prompt_type == PromptType.CMD:
            # Handle both enum and string values
            if isinstance(cmd_category, str):
                create_name = cmd_category + "_" + name
            else:
                create_name = cmd_category.value + "_" + name

        return create_name

    def parse_db_name(self, db_name: str, prompt_type: PromptType) -> str:
        """Extract the original filename from the database name

        Args:
            db_name: The database name
            (e.g., 'collect-approved-update_function.md')
            prompt_type: The type of prompt(PLAN or CMD)

        Returns:
            The original filename(e.g., 'update_function.md')
        """
        # split the name to a list using '_' seperator
        ls = db_name.split("_")
        # rebuild filename from the list of split words
        filename = ""
        if prompt_type == PromptType.PLAN:
            # if prompt type is PLAN: then name will include the project
            # so we need to drop the first 2 words in the db_name
            # example: collect_completed_add_claude_sdk_processing.md
            # ls = [collect, completed, add, claude, sdk, processing.md]
            for word in ls[2:]:
                if not word.endswith(".md"):
                    filename = filename + word + "_"
                else:
                    filename = filename + word
            return filename

        if prompt_type == PromptType.CMD:
            # if prompt type is CMD: then name will only include the dir/type
            # so we only need to drop the first word in ls
            # example: tools_create_database.md
            # ls = [tools, create, database.md]
            for word in ls[1:]:
                if not word.endswith(".md"):
                    filename = filename + word + "_"
                else:
                    filename = filename + word
            return filename

    def check_exists(self, name: str) -> Tuple[bool, str]:
        """Check if a prompt with the given name already exists

        Args:
            name: The prompt name to check

        Returns:
            Tuple[bool, str]: (exists, prompt_id)
            where exists is True if prompt exists,
            and prompt_id is the ID if found, empty string if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM prompt WHERE name = ?", (name,))
        result = cursor.fetchone()

        if result:
            return (True, result["id"])  # Found: return True and the prompt ID
        else:
            # Not found: return False and empty string
            return (False, "")

    def save_prompt_in_db(
        self, prompt: Prompt, change_summary: str = "Initial prompt creation"
    ) -> PromptCreateResult:
        """Create a new prompt and initialize version history
        if the prompt doesn't exist, if it already exists then
        we call `update_prompt_in_db` with the update.

        Args:
            prompt: Prompt object to create
            change_summary: Description of this change
            (default: "Initial prompt creation")

        Returns:
            PromptCreateResult: Success/failure with details
        """
        try:
            # Validate prompt has required fields
            if not prompt.id or not prompt.name or not prompt.data:
                return PromptCreateResult(
                    success=False,
                    prompt_id=prompt.id if prompt.id else "",
                    version=prompt.version if prompt.version else 1,
                    error_message="Prompt missing required fields",
                    error="ValidationError",
                )

            exists, prompt_id = self.check_exists(prompt.name)
            if exists:
                # get prompt from database using prompt_id from the version
                # retrieved from the database
                prompt_from_db = self.get_prompt_by_id(prompt_id)
                # if we don't have a prompt here then we return false
                if prompt_from_db is None:
                    return PromptCreateResult(
                        success=False,
                        prompt_id=prompt.id,
                        version=prompt.version,
                        error_message=f"prompt retrieval failed for {
                            prompt_id}",
                        error="ValueError",
                    )

                # otherwise we have a prompt from the database call
                # and we need to compare hashes to see if there are changes
                if prompt.content_hash == prompt_from_db.content_hash:
                    # if they are the same then the version in the db is the
                    # same as the version on disk so we return success and
                    # do nothing else.
                    return PromptCreateResult(
                        success=True,
                        prompt_id=prompt.id,
                        version=prompt.version,
                        error_message=f"""
                        prompt: {prompt.name} from disk is the same as db
                        """,
                        error="",
                    )

                else:
                    # if we get here then we have changes on disk that are more
                    # current than what is in the database

                    # IMPORTANT: We override the prompt.id here because the
                    # prompt exists already and we don't have a clean way of
                    # storing the uuid with the prompt on disk.
                    # When the prompt model is created from loading from disk,
                    # we DO generate a uuid for the model at that time just in
                    # case the prompt is newly generated from the disk and is
                    # not in the db
                    prompt.id = prompt_from_db.id

                    # Important to note that we will increment the version in
                    # `self.update_prompt_in_db`, we do not increment it here
                    return self.update_prompt_in_db(prompt)

            else:  # prompt doesn't exist in the database
                # if we make it here we have a new prompt and it
                # needs to be saved to the database for the first time
                prompt_jsonb = prompt.data.model_dump_json()

                # Create new cursor for this transaction
                cursor = self.conn.cursor()

                # insert prompt into prompt table
                cursor.execute(
                    """
                    INSERT INTO prompt(
                    id,
                    name,
                    data,
                    version,
                    content_hash,
                    created_at,
                    updated_at,
                    github_url
                    )
                    VALUES(?, ?, jsonb(?), ?, ?, ?, ?,?)
                    """,
                    (
                        prompt.id,
                        prompt.name,
                        prompt_jsonb,
                        prompt.version,
                        prompt.content_hash,
                        prompt.created_at,
                        prompt.updated_at,
                        prompt.github_url,
                    ),
                )

                # insert initial version into prompt_history table
                cursor.execute(
                    """
                    INSERT INTO prompt_history(
                    id,
                    version,
                    data,
                    content_hash,
                    created_at,
                    archived_at,
                    change_summary,
                    github_url
                    )
                    VALUES(?, ?, jsonb(?), ?, ?, ?, ?, ?)
                    """,
                    (
                        prompt.id,
                        prompt.version,
                        prompt_jsonb,
                        prompt.content_hash,
                        prompt.created_at,
                        datetime.now(timezone.utc),
                        change_summary,
                        prompt.github_url,
                    ),
                )
                self.conn.commit()

                return PromptCreateResult(
                    success=True, prompt_id=prompt.id, version=prompt.version
                )

        except Exception as e:
            self.conn.rollback()
            return PromptCreateResult(
                success=False,
                prompt_id=prompt.id,
                version=prompt.version,
                error_message=str(e),
                error=type(e).__name__,
            )

    def update_prompt_in_db(
        self, prompt: Prompt, change_summary: str = "Prompt updated from disk"
    ) -> PromptCreateResult:
        """Update an existing prompt and add to version history

        Args:
            prompt: Prompt object to update
            change_summary: Description of this change

        Returns:
            PromptCreateResult: Success/failure with details
        """
        try:
            cursor = self.conn.cursor()

            # first we get the existing prompt in the database
            current_prompt = self.get_prompt_by_id(prompt.id)
            if not current_prompt:
                return PromptCreateResult(
                    success=False,
                    prompt_id=prompt.id,
                    version=prompt.version,
                    error_message=f"Prompt w id {prompt.id} not found",
                    error="NotFoundError",
                )
            # then we increment the version
            prompt.version = current_prompt.version + 1

            # we need to recalculate the hash for the udpated prompt
            # so we can properly compare for changes
            prompt.content_hash = hashlib.sha256(
                prompt.data.content.encode("utf-8")
            ).hexdigest()

            # process the PromptData model to to json
            prompt_jsonb = prompt.data.model_dump_json()

            # then we update the `updated_at` timestamp
            prompt.updated_at = datetime.now(timezone.utc)

            # Update prompt table
            # NOTE: when writing the the jsonb field `data` we use jsonb
            # when reading we use `json(data)`
            cursor.execute(
                """
                UPDATE prompt
                SET name = ?,
                    data = jsonb(?),
                    version = ?,
                    content_hash = ?,
                    updated_at = ?,
                    github_url = ?
                WHERE id = ?
                """,
                (
                    prompt.name,
                    prompt_jsonb,
                    prompt.version,
                    prompt.content_hash,
                    prompt.updated_at,
                    prompt.github_url,
                    prompt.id,
                ),
            )

            # Insert into the updated prompt into prompt_history
            cursor.execute(
                """
                INSERT INTO prompt_history(
                id,
                version,
                data,
                content_hash,
                created_at,
                archived_at,
                change_summary,
                github_url)
                VALUES(?, ?, jsonb(?), ?, ?, ?, ?, ?)
                """,
                (
                    prompt.id,
                    prompt.version,
                    prompt_jsonb,
                    prompt.content_hash,
                    prompt.created_at,
                    datetime.now(timezone.utc),
                    change_summary,
                    prompt.github_url,
                ),
            )

            self.conn.commit()

            return PromptCreateResult(
                success=True, prompt_id=prompt.id, version=prompt.version
            )

        except Exception as e:
            self.conn.rollback()
            return PromptCreateResult(
                success=False,
                prompt_id=prompt.id,
                version=prompt.version,
                error_message=str(e),
                error=type(e).__name__,
            )

    def get_prompt_by_id(self, prompt_id: str) -> Optional[Prompt]:
        """Get a prompt by its ID from the database

        Args:
            prompt_id: The ID of the prompt to retrieve

        Returns:
            Optional[Prompt]: The prompt if found, None otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT
            id,
            name,
            json(data) as data_json,
            version,
            content_hash,
            created_at,
            updated_at,
            github_url

            FROM prompt
            WHERE id = ?
            """,
            (prompt_id,),
        )

        row = cursor.fetchone()
        if not row:
            return None

        # Parse the JSONB data back to PromptData
        data_dict = json.loads(row["data_json"])
        prompt_data = PromptData(**data_dict)

        # Create and return the Prompt object
        return Prompt(
            id=row["id"],
            name=row["name"],
            github_url=row["github_url"],
            data=prompt_data,
            version=row["version"],
            content_hash=row["content_hash"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_prompt_by_name(self, prompt_name: str) -> Optional[Prompt]:
        """
        Get a prompt by name from the database

        Args:
            prompt_name: The name of the prompt to retrieve.
            (should be unique)
        Returns:
            Optional[Prompt]: The prompt if found by name or None otherwise
        """

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT
            id,
            name,
            json(data) as data_json,
            version,
            content_hash,
            created_at,
            updated_at,
            github_url

            FROM prompt
            WHERE name = ?
            """,
            (prompt_name,),
        )

        row = cursor.fetchone()
        if not row:
            return None

        data_dict = json.loads(row["data_json"])
        prompt_data = PromptData(**data_dict)

        return Prompt(
            id=row["id"],
            name=row["name"],
            github_url=row["github_url"],
            data=prompt_data,
            version=row["version"],
            content_hash=row["content_hash"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def delete_prompt_by_id(self, prompt_id: str) -> PromptDeleteResult:
        cursor = self.conn.cursor()
        try:
            # archive final state in prompt_history table before deletion
            # we will not be deleting the version history of the prompt
            cursor.execute(
                """
                INSERT INTO prompt_history (
                id,
                version,
                data,
                content_hash,
                created_at,
                archived_at,
                change_summary,
                github_url)
                SELECT id, version, data, content_hash, created_at, ?, ?, github_url
                FROM prompt WHERE id = ?
            """,
                (datetime.now(timezone.utc), "DELETED - Final Version", prompt_id),
            )

            # Delete only from the prompt table
            cursor.execute("DELETE FROM prompt WHERE id = ?", (prompt_id,))
            deleted_row_count = cursor.rowcount

            self.conn.commit()

            return PromptDeleteResult(
                success=True,
                prompt_id=prompt_id,
                deleted=True,
                rows_affected=deleted_row_count,
            )

        except Exception as e:
            self.conn.rollback()
            return PromptDeleteResult(
                success=False,
                prompt_id=prompt_id,
                deleted=False,
                rows_affected=0,
                error_message=str(e),
                error_type=type(e).__name__,
            )

    def bulk_save_in_db(self, prompts: List[Prompt]) -> List[PromptCreateResult]:
        """
        Bulk load/save prompts into the database

        Args:
            plans: List of Plan objects to load into database

        Returns:
            PlanLoadResult: Summary of the loading operation
        """

        return [self.save_prompt_in_db(prompt) for prompt in prompts]

    def flatten_cmds_to_disk(self) -> List[PromptFlattenResult]:
        """Flatten all cmd_category prompts from database to disk directories

        Queries all CMD type prompts from database and writes them to:
        - .claude/commands/{category}/{filename}
        - .gemini/commands/{category}/{filename}

        Returns:
            List[PromptFlattenResult]: Individual results for each file written
        """
        results = []

        try:
            # Ensure command directories exist
            if not self.cmd_check_dirs():
                results.append(
                    PromptFlattenResult(
                        success=False,
                        prompt_id="",
                        prompt_name="",
                        file_path="",
                        cmd_category="",
                        error_message="Failed to create command directories",
                        error_type="DirectoryError",
                    )
                )
                return results

            # Query all CMD type prompts from database
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    json(data) as data_json,
                    version,
                    content_hash,
                    created_at,
                    updated_at,
                    github_url
                FROM prompt
                WHERE data ->> '$.type' = 'cmd'
                ORDER BY name
            """
            )

            rows = cursor.fetchall()

            if not rows:
                results.append(
                    PromptFlattenResult(
                        success=True,
                        prompt_id="",
                        prompt_name="",
                        file_path="",
                        cmd_category="",
                        error_message="No CMD prompts found in database",
                        error_type="",
                    )
                )
                return results

            project_dir = Path(__file__).parent.parent

            for row in rows:
                try:
                    # Parse the JSONB data back to PromptData
                    data_dict = json.loads(row["data_json"])
                    # `**` unpacks the dictionary into key words for pydantic
                    prompt_data = PromptData(**data_dict)

                    # Create Prompt object
                    prompt = Prompt(
                        id=row["id"],
                        name=row["name"],
                        github_url=row["github_url"],
                        data=prompt_data,
                        version=row["version"],
                        content_hash=row["content_hash"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )

                    # Get original filename from database name
                    filename = self.parse_db_name(prompt.name, PromptType.CMD)

                    # Get category, handle None/uncategorized case
                    if prompt.data.cmd_category:
                        if isinstance(prompt.data.cmd_category, str):
                            category = prompt.data.cmd_category
                        else:
                            category = prompt.data.cmd_category.value
                    else:
                        category = "uncategorized"

                    # Determine target directory based on tags
                    target_dirs = []
                    if prompt.data.tags:
                        if "claude" in prompt.data.tags:
                            target_dirs.append("claude")
                        if "gemini" in prompt.data.tags:
                            target_dirs.append("gemini")

                    # If no source tags found, skip this prompt
                    if not target_dirs:
                        errmsg = "No source tag (claude/gemini) found in tags"
                        results.append(
                            PromptFlattenResult(
                                success=False,
                                prompt_id=prompt.id,
                                prompt_name=prompt.name,
                                file_path="",
                                cmd_category=category,
                                error_message=errmsg,
                                error_type="MissingSourceTag",
                            )
                        )
                        continue

                    # Write to appropriate directories based on source tags
                    for target_dir in target_dirs:
                        try:
                            target_path = (
                                project_dir
                                / f".{target_dir}"
                                / "commands"
                                / category
                                / filename
                            )

                            # Ensure parent directory exists
                            target_path.parent.mkdir(parents=True, exist_ok=True)

                            # Write content to file
                            target_path.write_text(
                                prompt.data.content, encoding="utf-8"
                            )

                            results.append(
                                PromptFlattenResult(
                                    success=True,
                                    prompt_id=prompt.id,
                                    prompt_name=prompt.name,
                                    file_path=str(target_path),
                                    cmd_category=category,
                                    error_message="",
                                    error_type="",
                                )
                            )

                        except Exception as e:
                            results.append(
                                PromptFlattenResult(
                                    success=False,
                                    prompt_id=prompt.id,
                                    prompt_name=prompt.name,
                                    file_path=(
                                        str(target_path)
                                        if "target_path" in locals()
                                        else ""
                                    ),
                                    cmd_category=category,
                                    error_message=str(e),
                                    error_type=type(e).__name__,
                                )
                            )

                except Exception as e:
                    results.append(
                        PromptFlattenResult(
                            success=False,
                            prompt_id=row.get("id", ""),
                            prompt_name=row.get("name", ""),
                            file_path="",
                            cmd_category="",
                            error_message=f"Failed to process prompt: {
                                str(e)}",
                            error_type=type(e).__name__,
                        )
                    )

        except Exception as e:
            results.append(
                PromptFlattenResult(
                    success=False,
                    prompt_id="",
                    prompt_name="",
                    file_path="",
                    cmd_category="",
                    error_message=f"Database query failed: {str(e)}",
                    error_type=type(e).__name__,
                )
            )

        return results

    def flatten_plans_to_disk(self) -> List[PromptFlattenResult]:
        """Flatten all plan prompts from database to disk directories

        Queries all PLAN type prompts from database and writes them to:
        - _docs/plans/drafts/{filename}
        - _docs/plans/approved/{filename}
        - _docs/plans/completed/{filename}

        Returns:
            List[PromptFlattenResult]: Individual results for each file written
        """
        results = []

        try:
            # Ensure plan directories exist
            if not self.plans_check_dirs():
                results.append(
                    PromptFlattenResult(
                        success=False,
                        prompt_id="",
                        prompt_name="",
                        file_path="",
                        cmd_category="",
                        error_message="Failed to create plan directories",
                        error_type="DirectoryError",
                    )
                )
                return results

            # Query all PLAN type prompts from database
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    json(data) as data_json,
                    version,
                    content_hash,
                    created_at,
                    updated_at,
                    github_url
                FROM prompt
                WHERE data ->> '$.type' = 'plan'
                ORDER BY name
            """
            )

            rows = cursor.fetchall()

            if not rows:
                results.append(
                    PromptFlattenResult(
                        success=True,
                        prompt_id="",
                        prompt_name="",
                        file_path="",
                        cmd_category="",
                        error_message="No PLAN prompts found in database",
                        error_type="",
                    )
                )
                return results

            project_dir = Path(__file__).parent.parent

            # Status to directory mapping
            status_dir_mapping = {
                PromptPlanStatus.DRAFT.value: "drafts",
                PromptPlanStatus.APPROVED.value: "approved",
                PromptPlanStatus.COMPLETED.value: "completed",
            }

            for row in rows:
                try:
                    # Parse the JSONB data back to PromptData
                    data_dict = json.loads(row["data_json"])
                    prompt_data = PromptData(**data_dict)

                    # Create Prompt object
                    prompt = Prompt(
                        id=row["id"],
                        name=row["name"],
                        github_url=row["github_url"],
                        data=prompt_data,
                        version=row["version"],
                        content_hash=row["content_hash"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )

                    # Validate project name for PLAN type prompts
                    if not prompt.data.project:
                        # PLAN type must have a project name
                        results.append(
                            PromptFlattenResult(
                                success=False,
                                prompt_id=prompt.id,
                                prompt_name=prompt.name,
                                file_path="",
                                cmd_category="",
                                error_message="PLAN type prompt missing required project name",
                                error_type="MissingProjectError",
                            )
                        )
                        continue

                    # TODO: update this to use coordinate the github_url
                    if prompt.data.project != project_dir.name:
                        # Skip this prompt - it belongs to a different project
                        continue

                    # Get original filename from database name
                    filename = self.parse_db_name(prompt.name, PromptType.PLAN)

                    # Get status directory
                    status_value = (
                        prompt.data.status.value
                        if hasattr(prompt.data.status, "value")
                        else str(prompt.data.status)
                    )
                    status_dir = status_dir_mapping.get(status_value, "drafts")

                    # Write to appropriate status directory
                    try:
                        target_path = (
                            project_dir / "_docs" / "plans" / status_dir / filename
                        )

                        # Ensure parent directory exists
                        target_path.parent.mkdir(parents=True, exist_ok=True)

                        # Write content to file
                        target_path.write_text(prompt.data.content, encoding="utf-8")

                        results.append(
                            PromptFlattenResult(
                                success=True,
                                prompt_id=prompt.id,
                                prompt_name=prompt.name,
                                file_path=str(target_path),
                                cmd_category=status_dir,
                                error_message="",
                                error_type="",
                            )
                        )

                    except Exception as e:
                        results.append(
                            PromptFlattenResult(
                                success=False,
                                prompt_id=prompt.id,
                                prompt_name=prompt.name,
                                file_path=(
                                    str(target_path)
                                    if "target_path" in locals()
                                    else ""
                                ),
                                cmd_category=status_dir,
                                error_message=str(e),
                                error_type=type(e).__name__,
                            )
                        )

                except Exception as e:
                    results.append(
                        PromptFlattenResult(
                            success=False,
                            prompt_id=row.get("id", ""),
                            prompt_name=row.get("name", ""),
                            file_path="",
                            cmd_category="",
                            error_message=f"Failed to process prompt: {
                                str(e)}",
                            error_type=type(e).__name__,
                        )
                    )

        except Exception as e:
            results.append(
                PromptFlattenResult(
                    success=False,
                    prompt_id="",
                    prompt_name="",
                    file_path="",
                    cmd_category="",
                    error_message=f"Database query failed: {str(e)}",
                    error_type=type(e).__name__,
                )
            )

        return results
