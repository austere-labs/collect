import json
import uuid
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from repository.database import SQLite3Database
from repository.prompt_model import PromptCreateModel, PromptResponseModel


class PromptService:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / "data" / "collect.db")
        self.db = SQLite3Database(db_path=db_path)

    def add_prompt(self, prompt_data: PromptCreateModel) -> str:
        prompt_uuid = str(uuid.uuid4())

        metadata = prompt_data.metadata.copy()
        metadata["name"] = prompt_data.name
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
                    SELECT id, prompt_uuid, version, content, metadata, created_at, updated_at, is_active
                    FROM prompts
                    WHERE prompt_uuid = ? AND version = ?
                    """,
                    (prompt_uuid, version)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT id, prompt_uuid, version, content, metadata, created_at, updated_at, is_active
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
                SELECT id, prompt_uuid, version, content, metadata, created_at, updated_at, is_active
                FROM prompts
                WHERE is_active = 1
                ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()

            return [self._row_to_model(row) for row in rows]

    def deactivate_prompt(self, prompt_uuid: str, version: Optional[int] = None) -> bool:
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
