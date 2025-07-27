import sqlite3
from pathlib import Path
import uuid
import json
from datetime import datetime
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
)


class PromptService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
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
            plans_dir / "completed"
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
                    print(f"   ✅ Created: {
                          missing_dir.relative_to(project_dir)}")
                except Exception as e:
                    print(f"   ❌ Failed to create {
                          missing_dir.relative_to(project_dir)}: {e}")
                    return False

            if created_dirs:
                print(f"📁 Successfully created {
                      len(created_dirs)} directories")
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
        commands_dir = claude_dir / "commands"

        # Required directories
        required_dirs = [
            commands_dir,
            commands_dir / "archive",
            commands_dir / "go",
            commands_dir / "js",
            commands_dir / "mcp",
            commands_dir / "python",
            commands_dir / "tools"
        ]
        missing_dirs = []
        created_dirs = []

        # get missing dirs and add any to missing_dirs list
        for dir_path in required_dirs:
            if not dir_path.exists():
                missing_dirs.append(dir_path)

        if missing_dirs:
            print("📁 Creating missing command directories:")
            for missing_dir in missing_dirs:
                try:
                    missing_dir.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(missing_dir)
                    print(f"   ✅ Created: {
                          missing_dir.relative_to(claude_dir)}")
                except Exception as e:
                    print(f"   ❌ Failed to create {
                          missing_dir.relative_to(claude_dir)}: {e}")
                    return False

            if created_dirs:
                print(f"📁 Successfully created {
                      len(created_dirs)} directories")
        else:
            print("✅ All required command directories exist")

        return True

    def load_cmds_from_disk(self) -> PromptLoadResult:
        cmds_dir = Path(__file__).parent.parent / ".claude" / "commands"
        prompts = []
        errors = []

        # loop through the files in cmds dir and load prompts first
        for file in cmds_dir.iterdir():
            if file.is_file() and file.suffix == '.md':
                try:
                    # Check if filename adheres to naming rules
                    current_filename = file.name
                    if not self.check_filename(current_filename):
                        # Normalize the filename
                        fixed_filename = self.normalize_filename(
                            current_filename)

                        # Create new file path with normalized name
                        new_file_path = file.parent / fixed_filename

                        # Rename the file on disk
                        file.rename(new_file_path)

                        # Update file reference to the new path
                        file = new_file_path
                        print(
                            f"""
                            📝 Renamed: {current_filename} → {fixed_filename}
                            """
                        )

                    prompt_content = file.read_text()
                    prompt = self.new_prompt_model(
                        prompt_content=prompt_content,
                        name=file.name,
                        prompt_type=PromptType.CMD,
                        cmd_category=CmdCategory.UNCATEGORIZED,
                        status=PromptPlanStatus.DRAFT,
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

        # then cycle through the subdirs, create Prompt models and append
        for sub_dir in cmds_dir.iterdir():
            if sub_dir.is_dir():
                cmd_category = CmdCategory(sub_dir.name.lower())

                for file in sub_dir.iterdir():
                    try:
                        if file.is_file() and file.suffix == '.md':
                            # Check if filename adheres to naming rules
                            current_filename = file.name
                            if not self.check_filename(current_filename):
                                # Normalize the filename
                                fixed_filename = self.normalize_filename(
                                    current_filename)

                                # Create new file path with normalized name
                                new_file_path = file.parent / fixed_filename

                                # Rename the file on disk
                                file.rename(new_file_path)

                                # Update file reference to the new path
                                file = new_file_path
                                print(
                                    f"""
                                    📝 Renamed: {current_filename} → {fixed_filename}
                                    """
                                )

                            prompt_content = file.read_text()
                            prompt_type = PromptType.CMD
                            status = PromptPlanStatus.DRAFT

                            prompt = self.new_prompt_model(
                                prompt_content=prompt_content,
                                name=file.name,
                                prompt_type=prompt_type,
                                cmd_category=cmd_category,
                                status=status,
                            )
                            prompts.append(prompt)

                    except Exception as e:
                        errors.append(
                            LoadError(
                                filename=str(file),
                                error_message=str(e),
                                error_type=type(e).__name__
                            )
                        )
        return PromptLoadResult(
            loaded_prompts=prompts,
            errors=errors,
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
                        if file.is_file() and file.suffix == '.md':
                            # Check if filename adheres to naming rules
                            current_filename = file.name
                            if not self.check_filename(current_filename):
                                # Normalize the filename
                                fixed_filename = self.normalize_filename(
                                    current_filename)

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
                                    cmd_category=cmd_category,
                                    status=status,
                                    project=project_dir.name,
                                ))

                    except Exception as e:
                        errors.append(
                            LoadError(
                                filename=str(file),
                                error_message=str(e),
                                error_type=type(e).__name__
                            )
                        )

        return PromptLoadResult(
            loaded_prompts=prompts,
            errors=errors
        )

    def normalize_filename(self, filename: str) -> str:
        """Normalize filename to use underscores and ensure .md extension

        Args:
            filename: The original filename

        Returns:
            Normalized filename with underscores and .md extension
        """
        # Replace hyphens with underscores
        normalized = filename.replace('-', '_')

        # Ensure .md extension
        if not normalized.endswith('.md'):
            # Remove any existing extension and add .md
            if '.' in normalized:
                normalized = normalized.rsplit('.', 1)[0] + '.md'
            else:
                normalized = normalized + '.md'

        return normalized

    def check_filename(self, filename: str) -> bool:
        """Check if filename adheres to naming rules
        (underscores and .md extension)

        Args:
            filename: The filename to check

        Returns:
            bool: True if filename follows the rules, False otherwise
        """
        # Check if filename has .md extension
        if not filename.endswith('.md'):
            return False

        # Check if filename contains hyphens (should use underscores)
        if '-' in filename:
            return False

        return True

    def new_prompt_model(
            self,
            prompt_content: str,
            name: str,
            prompt_type: PromptType,
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
            default_tags.append(cmd_category.value)
        default_tags.append(prompt_type.value)

        prompt_data = PromptData(
            type=prompt_type,
            status=status,
            project=project,
            cmd_category=cmd_category,
            content=prompt_content,
            description=description,
            tags=default_tags,
        )

        content_hash = hashlib.sha256(
            prompt_content.encode('utf-8')
        ).hexdigest()

        timestamp = datetime.utcnow()

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
        ls = db_name.split('_')
        # rebuild filename from ls
        filename = ""
        if prompt_type == PromptType.PLAN:
            # if prompt type is PLAN: then name will include the project
            # so we need to drop the first 2 words in the db_name
            # example: collect_completed_add_claude_sdk_processing.md
            # ls = [collect, completed, add, claude, sdk, processing.md]
            for word in ls[2:]:
                if not word.endswith('.md'):
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
                if not word.endswith('.md'):
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
            return (True, result[0])  # Found: return True and the prompt ID
        else:
            # Not found: return False and empty string
            return (False, "")

    def save_prompt_in_db(
        self,
        prompt: Prompt,
        change_summary: str = "Initial prompt creation"
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
                    error="ValidationError"
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
                    # we increment the version here because the updated prompt
                    # will be version +1 in the `prompt` table and we will
                    # update prompt history with the latest version as well
                    # so we have a complete history for the prompt in the
                    # `prompt_history` table. This IS redundant storage of the
                    # same prompt, but it makes it easier when looking at
                    # the prompt_history table to see the entire history
                    prompt.version = prompt_from_db.version + 1

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
                    id, name, data, version, content_hash, created_at, updated_at
                    )
                    VALUES(?, ?, jsonb(?), ?, ?, ?, ?)
                    """, (
                        prompt.id,
                        prompt.name,
                        prompt_jsonb,
                        prompt.version,
                        prompt.content_hash,
                        prompt.created_at,
                        prompt.updated_at
                    ))

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
                    change_summary
                    )
                    VALUES(?, ?, jsonb(?), ?, ?, ?, ?)
                    """, (
                        prompt.id,
                        prompt.version,
                        prompt_jsonb,
                        prompt.content_hash,
                        prompt.created_at,
                        datetime.utcnow(),
                        change_summary,
                    ))
                self.conn.commit()

                return PromptCreateResult(
                    success=True,
                    prompt_id=prompt.id,
                    version=prompt.version
                )

        except Exception as e:
            self.conn.rollback()
            return PromptCreateResult(
                success=False,
                prompt_id=prompt.id,
                version=prompt.version,
                error_message=str(e),
                error=type(e).__name__
            )

    def update_prompt_in_db(
            self, prompt: Prompt,
            change_summary: str = "Prompt updated from disk"
    ) -> PromptCreateResult:
        """Update an existing prompt and add to version history

        Args:
            prompt: Prompt object to update
            change_summary: Description of this change

        Returns:
            PromptCreateResult: Success/failure with details
        """
        try:
            prompt_jsonb = prompt.data.model_dump_json()
            cursor = self.conn.cursor()

            # Update prompt table
            cursor.execute(
                """
                UPDATE prompt
                SET name = ?,
                    data = jsonb(?),
                    version = version,
                    content_hash = ?,
                    updated_at = ?
                WHERE id = ?
                """, (
                    prompt.name,
                    prompt_jsonb,
                    prompt.content_hash,
                    prompt.updated_at,
                    prompt.id
                ))

            # Insert into prompt_history
            cursor.execute(
                """
                INSERT INTO prompt_history(
                id,
                version,
                data,
                content_hash,
                created_at,
                )
                VALUES(?, ?, jsonb(?), ?, ?, ?, ?)
                """, (
                    prompt.id,
                    prompt.version,
                    prompt_jsonb,
                    prompt.content_hash,
                    prompt.created_at,
                    datetime.utcnow(),
                    change_summary
                ))

            self.conn.commit()

            return PromptCreateResult(
                success=True,
                prompt_id=prompt.id,
                version=prompt.version + 1
            )

        except Exception as e:
            self.conn.rollback()
            return PromptCreateResult(
                success=False,
                prompt_id=prompt.id,
                version=prompt.version,
                error_message=str(e),
                error=type(e).__name__
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
            id, name, data, version, content_hash, created_at, updated_at
            FROM prompt
            WHERE id = ?
            """,
            (prompt_id,)
        )
        result = cursor.fetchone()

        if not result:
            return None

        # Unpack the result
        id, name, data_json, version, content_hash, created_at, updated_at = result

        # Parse the JSONB data back to PromptData
        data_dict = json.loads(data_json)
        prompt_data = PromptData(**data_dict)

        # Create and return the Prompt object
        return Prompt(
            id=id,
            name=name,
            data=prompt_data,
            version=version,
            content_hash=content_hash,
            created_at=created_at,
            updated_at=updated_at
        )

    def delete_prompt_by_id(self, prompt_id: str) -> PromptDeleteResult:
        cursor = self.conn.cursor()
        # archive final state in prompt_history table before deletion
        cursor.execute("""
            INSERT INTO prompt_history (
            id,
            version,
            data,
            content_hash,
            created_at,
            change_summary)
            SELECT id, version, data, content_hash, craeted_at, 'DELETED - Final Version'
            FROM prompt WHERE id = ?
        """, (prompt_id, ))

        # Delete only from the prompt table
        cursor.execute("DELETE FROM prompt where id = ?", (prompt_id, ))

    def load_database(self, prompts: List[Prompt]) -> PromptLoadResult:
        """Load plans into the database

        Args:
            plans: List of Plan objects to load into database

        Returns:
            PlanLoadResult: Summary of the loading operation
        """
