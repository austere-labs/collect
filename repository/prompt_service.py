import json
import uuid
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from repository.database import SQLite3Database
from repository.prompt_model import (
    PromptCreateModel,
    PromptResponseModel,
    LoadResult,
    FileError
)


class PromptService:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / "data" / "collect.db")
        self.db = SQLite3Database(db_path=db_path)

    # This will load all of the prompts from .claude/commands
    def load_claude_commands_from_disk(self) -> LoadResult:
        # __file__ is a ref to the this file: repository/prompt_service.py
        # this should render: collect/.claude/commands
        prompts_dir = Path(__file__).parent.parent / ".claude" / "commands"
        files_dict = {}
        errors = []
        for file in prompts_dir.iterdir():
            if file.is_file():
                try:
                    content = file.read_text()
                    name = file.name  # file.name includes the file extension
                    files_dict[name] = content
                except Exception as e:
                    errors.append(
                        FileError(
                            filename=str(file),
                            error_message=str(e),
                            error_type=type(e).__name__
                        )
                    )

        return LoadResult(files=files_dict, errors=errors)

    def persist_load_results(
            self,
            load_result: LoadResult,
            initial_load: bool = False) -> List[str]:

        files = load_result.files
        persisted_prompt_uuids = []
        for filename, prompt in files.items():
            prompt_data = PromptCreateModel(
                name=filename,
                content=prompt
            )
            # if this is an initial load then we load all prompts in as v1
            # v1 is defaulted for a new insert in the prompts table
            if initial_load is True:
                uuid = self.add_prompt(prompt_data)
                persisted_prompt_uuids.append(uuid)
            else:
                self.compare_disk_to_db()

        return persisted_prompt_uuids

    def compare_disk_to_db(self) -> str:
        return """
        TODO: compare prompts on disk to prompts in db, if changes on disk
        increment version in database and update the prompt in the database
        IF: there are new prompts on disk, then we persist them with version 1
        using add_prompt
        """

    def update_prompt_increment_version(self):
        return """
        TODO: take prompt model ->
        CREATE a new prompt with same UUID and incremental version
        """

    def add_prompt(self, prompt_data: PromptCreateModel) -> str:
        prompt_uuid = str(uuid.uuid4())

        metadata = prompt_data.metadata.copy()
        metadata["name"] = prompt_data.name
        print("TODO: add prompt description, use llm to create")
        metadata_json = json.dumps(metadata)

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO prompts (prompt_uuid, version, content, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (prompt_uuid, 1, prompt_data.content, metadata_json)
            )

        return prompt_uuid

    def get_prompt_by_name(self, name: str) -> Optional[PromptResponseModel]:
        with self.db.get_connection(read_only=True) as conn:
            cursor = conn.execute(
                """
                SELECT
                id,
                prompt_uuid,
                version,
                content,
                metadata,
                created_at,
                updated_at, is_active

                FROM prompts
                WHERE JSON_EXTRACT(metadata, '$.name') = ? AND is_active = 1
                ORDER BY version DESC
                LIMIT 1
                """,
                (name,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_model(row)
            return None

    def get_prompt_by_uuid(
            self,
            prompt_uuid: str,
            version: Optional[int] = None) -> Optional[PromptResponseModel]:

        with self.db.get_connection(read_only=True) as conn:
            if version is not None:
                cursor = conn.execute(
                    """
                    SELECT
                    id,
                    prompt_uuid,
                    version,
                    content,
                    metadata,
                    created_at,
                    updated_at, is_active

                    FROM prompts
                    WHERE prompt_uuid = ? AND version = ?
                    """,
                    (prompt_uuid, version)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT
                    id,
                    prompt_uuid,
                    version,
                    content,
                    metadata,
                    created_at,
                    updated_at,
                    is_active

                    FROM prompts
                    WHERE prompt_uuid = ? AND is_active = 1
                    ORDER BY version DESC
                    LIMIT 1
                    """,
                    (prompt_uuid,)
                )

            row = cursor.fetchone()

            if row:
                return self._row_to_model(row)
            return None

    def list_prompts(self) -> List[PromptResponseModel]:
        with self.db.get_connection(read_only=True) as conn:
            cursor = conn.execute(
                """
                SELECT
                id,
                prompt_uuid,
                version,
                content,
                metadata,
                created_at,
                updated_at,
                is_active

                FROM prompts
                WHERE is_active = 1
                ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()

            return [self._row_to_model(row) for row in rows]

    def deactivate_prompt(
            self, prompt_uuid: str, version: Optional[int] = None) -> bool:

        with self.db.get_connection() as conn:
            if version is not None:
                cursor = conn.execute(
                    """
                    UPDATE prompts
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE prompt_uuid = ? AND version = ?
                    """,
                    (prompt_uuid, version)
                )
            else:
                cursor = conn.execute(
                    """
                    UPDATE prompts
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE prompt_uuid = ?
                    """,
                    (prompt_uuid,)
                )

            return cursor.rowcount > 0

    def _row_to_model(self, row) -> PromptResponseModel:
        return PromptResponseModel(
            id=row["id"],
            prompt_uuid=row["prompt_uuid"],
            version=row["version"],
            content=row["content"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=datetime.fromisoformat(
                row["created_at"]) if row["created_at"] else datetime.now(),
            updated_at=datetime.fromisoformat(
                row["updated_at"]) if row["updated_at"] else datetime.now(),
            is_active=bool(row["is_active"])
        )
