import pytest
import json
import os
from pathlib import Path

from repository.prompt_service import PromptService
from repository.prompt_model import PromptCreateModel


@pytest.fixture
def test_prompt_service():
    test_db_path = "test_prompt_service.db"
    
    # Create service with test database
    service = PromptService(db_path=test_db_path)
    
    # Create the prompts table for testing
    with service.db.get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_uuid TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                content TEXT NOT NULL,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                UNIQUE(prompt_uuid, version)
            )
        """)
    
    yield service
    
    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


def test_add_prompt_basic(test_prompt_service):
    service = test_prompt_service
    
    # Add a basic prompt
    prompt_data = PromptCreateModel(name="test_prompt", content="This is a test prompt")
    prompt_uuid = service.add_prompt(prompt_data)
    
    assert prompt_uuid is not None
    assert len(prompt_uuid) == 36  # UUID length
    
    # Verify it was stored correctly
    with service.db.get_connection(read_only=True) as conn:
        cursor = conn.execute(
            "SELECT prompt_uuid, content, metadata FROM prompts WHERE prompt_uuid = ?",
            (prompt_uuid,)
        )
        row = cursor.fetchone()
        
        assert row is not None
        assert row["prompt_uuid"] == prompt_uuid
        assert row["content"] == "This is a test prompt"
        metadata = json.loads(row["metadata"])
        assert metadata["name"] == "test_prompt"


def test_add_prompt_with_metadata(test_prompt_service):
    service = test_prompt_service
    
    # Add prompt with custom metadata
    custom_metadata = {"author": "test_user", "category": "testing"}
    prompt_data = PromptCreateModel(name="test_with_meta", content="Test content", metadata=custom_metadata)
    prompt_uuid = service.add_prompt(prompt_data)
    
    # Verify metadata was merged correctly
    with service.db.get_connection(read_only=True) as conn:
        cursor = conn.execute(
            "SELECT metadata FROM prompts WHERE prompt_uuid = ?",
            (prompt_uuid,)
        )
        row = cursor.fetchone()
        
        metadata = json.loads(row["metadata"])
        assert metadata["name"] == "test_with_meta"
        assert metadata["author"] == "test_user"
        assert metadata["category"] == "testing"


def test_get_prompt_by_name_exists(test_prompt_service):
    service = test_prompt_service
    
    # Add a prompt
    prompt_data = PromptCreateModel(name="find_me", content="Content to find")
    prompt_uuid = service.add_prompt(prompt_data)
    
    # Get by name
    result = service.get_prompt_by_name("find_me")
    
    assert result is not None
    assert result.prompt_uuid == prompt_uuid
    assert result.content == "Content to find"
    assert result.metadata["name"] == "find_me"
    assert result.version == 1
    assert result.is_active is True


def test_get_prompt_by_name_not_exists(test_prompt_service):
    service = test_prompt_service
    
    # Try to get non-existent prompt
    result = service.get_prompt_by_name("nonexistent")
    
    assert result is None


def test_get_prompt_by_uuid_exists(test_prompt_service):
    service = test_prompt_service
    
    # Add a prompt
    prompt_data = PromptCreateModel(name="uuid_test", content="UUID test content")
    prompt_uuid = service.add_prompt(prompt_data)
    
    # Get by UUID
    result = service.get_prompt_by_uuid(prompt_uuid)
    
    assert result is not None
    assert result.prompt_uuid == prompt_uuid
    assert result.content == "UUID test content"
    assert result.version == 1


def test_get_prompt_by_uuid_with_version(test_prompt_service):
    service = test_prompt_service
    
    # Add a prompt
    prompt_data = PromptCreateModel(name="version_test", content="Version test content")
    prompt_uuid = service.add_prompt(prompt_data)
    
    # Get by UUID and version
    result = service.get_prompt_by_uuid(prompt_uuid, version=1)
    
    assert result is not None
    assert result.prompt_uuid == prompt_uuid
    assert result.version == 1


def test_get_prompt_by_uuid_not_exists(test_prompt_service):
    service = test_prompt_service
    
    # Try to get non-existent UUID
    result = service.get_prompt_by_uuid("00000000-0000-0000-0000-000000000000")
    
    assert result is None


def test_list_prompts_empty(test_prompt_service):
    service = test_prompt_service
    
    # List when no prompts exist
    prompts = service.list_prompts()
    
    assert prompts == []


def test_list_prompts_with_data(test_prompt_service):
    service = test_prompt_service
    
    # Add multiple prompts
    prompt_data1 = PromptCreateModel(name="prompt1", content="Content 1")
    prompt_data2 = PromptCreateModel(name="prompt2", content="Content 2")
    uuid1 = service.add_prompt(prompt_data1)
    uuid2 = service.add_prompt(prompt_data2)
    
    # List prompts
    prompts = service.list_prompts()
    
    assert len(prompts) == 2
    
    # Check that both prompts are present
    prompt_uuids = [p.prompt_uuid for p in prompts]
    assert uuid1 in prompt_uuids
    assert uuid2 in prompt_uuids


def test_deactivate_prompt_by_uuid(test_prompt_service):
    service = test_prompt_service
    
    # Add a prompt
    prompt_data = PromptCreateModel(name="to_deactivate", content="Will be deactivated")
    prompt_uuid = service.add_prompt(prompt_data)
    
    # Verify it's active
    result = service.get_prompt_by_uuid(prompt_uuid)
    assert result.is_active is True
    
    # Deactivate it
    success = service.deactivate_prompt(prompt_uuid)
    assert success is True
    
    # Verify it's deactivated
    result = service.get_prompt_by_uuid(prompt_uuid)
    assert result is None  # Should not return inactive prompts
    
    # But should still exist in database
    with service.db.get_connection(read_only=True) as conn:
        cursor = conn.execute(
            "SELECT is_active FROM prompts WHERE prompt_uuid = ?",
            (prompt_uuid,)
        )
        row = cursor.fetchone()
        assert row["is_active"] == 0


def test_deactivate_prompt_by_uuid_and_version(test_prompt_service):
    service = test_prompt_service
    
    # Add a prompt
    prompt_data = PromptCreateModel(name="version_deactivate", content="Version deactivate test")
    prompt_uuid = service.add_prompt(prompt_data)
    
    # Deactivate specific version
    success = service.deactivate_prompt(prompt_uuid, version=1)
    assert success is True
    
    # Verify it's deactivated
    result = service.get_prompt_by_uuid(prompt_uuid, version=1)
    assert result is not None
    assert result.is_active is False


def test_deactivate_nonexistent_prompt(test_prompt_service):
    service = test_prompt_service
    
    # Try to deactivate non-existent prompt
    success = service.deactivate_prompt("00000000-0000-0000-0000-000000000000")
    assert success is False


def test_list_prompts_excludes_inactive(test_prompt_service):
    service = test_prompt_service
    
    # Add prompts
    prompt_data1 = PromptCreateModel(name="active", content="Active content")
    prompt_data2 = PromptCreateModel(name="inactive", content="Inactive content")
    uuid1 = service.add_prompt(prompt_data1)
    uuid2 = service.add_prompt(prompt_data2)
    
    # Deactivate one
    service.deactivate_prompt(uuid2)
    
    # List should only include active
    prompts = service.list_prompts()
    assert len(prompts) == 1
    assert prompts[0].prompt_uuid == uuid1


def test_get_prompt_by_name_excludes_inactive(test_prompt_service):
    service = test_prompt_service
    
    # Add and deactivate a prompt
    prompt_data = PromptCreateModel(name="inactive_test", content="Inactive test content")
    prompt_uuid = service.add_prompt(prompt_data)
    service.deactivate_prompt(prompt_uuid)
    
    # Should not find inactive prompt
    result = service.get_prompt_by_name("inactive_test")
    assert result is None


def test_database_path_default():
    # Test that default database path is constructed correctly
    service = PromptService()
    expected_path = str(Path(__file__).parent.parent / "data" / "collect.db")
    assert service.db.db_path == expected_path


def test_database_path_custom():
    # Test custom database path
    custom_path = "custom_test.db"
    service = PromptService(db_path=custom_path)
    assert service.db.db_path == custom_path
    
    # Cleanup
    if os.path.exists(custom_path):
        os.remove(custom_path)


def test_json_extraction_in_query(test_prompt_service):
    service = test_prompt_service
    
    # Add prompts with different names
    prompt_data1 = PromptCreateModel(name="test_name_1", content="Content 1")
    prompt_data2 = PromptCreateModel(name="test_name_2", content="Content 2")
    service.add_prompt(prompt_data1)
    service.add_prompt(prompt_data2)
    
    # Should only find exact name match
    result = service.get_prompt_by_name("test_name_1")
    assert result is not None
    assert result.content == "Content 1"
    
    result = service.get_prompt_by_name("test_name_2")
    assert result is not None
    assert result.content == "Content 2"
    
    # Should not find partial matches
    result = service.get_prompt_by_name("test_name")
    assert result is None