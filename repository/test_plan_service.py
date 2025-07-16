import pytest
from datetime import datetime
from repository.database import SQLite3Database
from repository.plan_service import PlanService
from repository.plan_models import Plan, PlanData, PlanStatus
from repository.test_database_setup import setup_test_database


@pytest.fixture(scope="function")
def test_database():
    """Set up test database for each test function."""
    db_path = setup_test_database()
    yield db_path
    # Note: We don't clean up the test database here to allow inspection after tests


@pytest.fixture
def test_plan_service(test_database):
    """Create a PlanService instance using the test database."""
    db = SQLite3Database(test_database)
    with db.get_connection() as conn:
        plan_service = PlanService(conn)
        yield plan_service


def test_check_dirs(test_plan_service):
    # Test the check_dirs method
    result = test_plan_service.check_dirs()
    assert result is True


def test_files_to_plans_conversion(test_plan_service):
    # Get raw plans data first
    plans_data, _ = test_plan_service.load_files()

    # Test the conversion method directly
    plans = test_plan_service.files_to_plans(plans_data)

    assert isinstance(plans, list)
    assert len(plans) > 0  # Should have plans from test data

    # Test specific plan properties
    for plan in plans:
        assert plan.version == 1
        assert len(plan.content_hash) == 64  # SHA256 hash length
        assert plan.id.startswith(plan.data.status.value)
        assert plan.data.status in ["draft", "approved", "completed"]
        assert len(plan.data.markdown_content) > 0
        assert plan.data.status.value in plan.data.tags

    print(f"✅ Validated {len(plans)} Plan objects")


def test_load_files(test_plan_service):
    # Test the load_files method that reads from _docs/plans
    plans_data, plans = test_plan_service.load_files()

    # Test that we get Plan objects
    assert isinstance(plans, list)
    assert len(plans) > 0

    # Test first plan object structure
    first_plan = plans[0]
    assert hasattr(first_plan, 'id')
    assert hasattr(first_plan, 'name')
    assert hasattr(first_plan, 'data')
    assert hasattr(first_plan, 'version')
    assert hasattr(first_plan, 'content_hash')
    assert hasattr(first_plan, 'created_at')
    assert hasattr(first_plan, 'updated_at')

    # Test PlanData structure
    assert hasattr(first_plan.data, 'status')
    assert hasattr(first_plan.data, 'markdown_content')
    assert len(first_plan.data.markdown_content) > 0

    print(f"✅ Successfully converted {len(plans)} plans")


def test_load_database(test_plan_service):
    # First load plans from files
    plans_data, plans = test_plan_service.load_files()

    # Get the expected count from the actual number of plans loaded
    expected_count = len(plans)

    # Test loading into database
    result = test_plan_service.load_database(plans)

    # Verify the result using dynamic count
    assert result.loaded_count == expected_count  # Should load all plans from disk
    assert result.skipped_count == 0  # First time loading, nothing to skip
    assert result.error_count == 0   # Should be no errors
    assert len(result.loaded_plans) == expected_count

    # Test that plans are actually in the database
    conn = test_plan_service.conn
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM plans")
    count = cursor.fetchone()[0]
    assert count == expected_count

    # Test loading same plans again (should skip)
    result2 = test_plan_service.load_database(plans)
    assert result2.loaded_count == 0   # Nothing new to load
    assert result2.skipped_count == expected_count  # All should be skipped
    assert result2.error_count == 0

    print(f"✅ Successfully loaded {result.loaded_count} plans to database")
    print(f"✅ Correctly skipped {result2.skipped_count} existing plans")


def test_sync_plans(test_plan_service):
    # Test the complete sync workflow
    result = test_plan_service.sync_plans()

    # Get expected count from the actual result (loaded + skipped)
    expected_total = result.loaded_count + result.skipped_count

    # Verify the sync worked (either loaded new plans or skipped existing ones)
    assert expected_total > 0  # Should have some plans total
    assert result.error_count == 0

    # Verify plans are in database
    conn = test_plan_service.conn
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM plans")
    count = cursor.fetchone()[0]
    assert count >= expected_total  # Should have at least the synced plans

    print(f"✅ Sync completed: {result.loaded_count} plans loaded, {
          result.skipped_count} plans skipped")


def test_database_connection(test_plan_service):
    conn = test_plan_service.conn
    cursor = conn.cursor()
    # Test: Try a simple insert/select
    cursor.execute("""
        INSERT INTO plans (id, name, data, content_hash)
        VALUES ('test-connection-1', 'Test Plan', '{"test": true}', 'hash123')
    """)

    cursor.execute("SELECT name FROM plans WHERE id = 'test-connection-1'")
    result = cursor.fetchone()
    assert result[0] == 'Test Plan'

    # Commit the test data - no need to clean up in separate test database
    conn.commit()


def test_check_exists(test_plan_service):
    """Test the check_exists function"""
    # Test non-existent plan
    assert test_plan_service.check_exists("non_existent_plan") is False

    # Create a test plan
    current_time = datetime.now()
    test_plan = Plan(
        id="test_check_exists_plan",
        name="Test Check Exists Plan",
        data=PlanData(
            status=PlanStatus.DRAFT,
            markdown_content="# Test Plan\n\nThis is a test plan for check_exists.",
            description="A test plan for check_exists function",
            tags=["test", "draft"]
        ),
        version=1,
        content_hash="check_exists_hash",
        created_at=current_time,
        updated_at=current_time
    )

    # Before creating the plan, it should not exist
    assert test_plan_service.check_exists(test_plan.id) is False

    # Create the plan
    result = test_plan_service.create_new_plan(
        test_plan, "Test creation for check_exists")
    assert result.success is True

    # After creating the plan, it should exist
    assert test_plan_service.check_exists(test_plan.id) is True

    # Test with different casing (should not exist)
    assert test_plan_service.check_exists("TEST_CHECK_EXISTS_PLAN") is False

    # Test with similar but different ID (should not exist)
    assert test_plan_service.check_exists("test_check_exists_plan_2") is False

    # No cleanup needed - using separate test database


def test_create_new_plan_success(test_plan_service):
    """Test successful creation of a new plan"""
    # Create a test plan
    current_time = datetime.now()
    test_plan = Plan(
        id="test_create_new_plan",
        name="Test Create New Plan",
        data=PlanData(
            status=PlanStatus.DRAFT,
            markdown_content="# Test Plan\n\nThis is a test plan.",
            description="A test plan for create_new_plan function",
            tags=["test", "draft"],
            metadata={"test": True}
        ),
        version=1,
        content_hash="abc123test",
        created_at=current_time,
        updated_at=current_time
    )

    # Create the plan
    result = test_plan_service.create_new_plan(test_plan, "Test creation")

    # Verify success
    assert result.success is True
    assert result.plan_id == "test_create_new_plan"
    assert result.version == 1
    assert result.error_message is None
    assert result.error_type is None

    # Verify plan exists in plans table
    conn = test_plan_service.conn
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plans WHERE id = ?", (test_plan.id,))
    plan_row = cursor.fetchone()

    assert plan_row is not None
    assert plan_row['id'] == test_plan.id
    assert plan_row['name'] == test_plan.name
    assert plan_row['version'] == 1
    assert plan_row['content_hash'] == test_plan.content_hash

    # Verify history entry exists
    cursor.execute("SELECT * FROM plan_history WHERE id = ? AND version = ?",
                   (test_plan.id, 1))
    history_row = cursor.fetchone()

    assert history_row is not None
    assert history_row['id'] == test_plan.id
    assert history_row['version'] == 1
    assert history_row['content_hash'] == test_plan.content_hash
    assert history_row['change_summary'] == "Test creation"
    assert history_row['created_at'] == current_time
    assert history_row['archived_at'] is not None

    # Cleanup
    cursor.execute("DELETE FROM plans WHERE id = ?", (test_plan.id,))
    cursor.execute("DELETE FROM plan_history WHERE id = ?", (test_plan.id,))
    conn.commit()


def test_create_new_plan_duplicate_id(test_plan_service):
    """Test creating a plan with duplicate ID"""
    # Create a test plan
    current_time = datetime.now()
    test_plan = Plan(
        id="test_duplicate_plan",
        name="Test Duplicate Plan",
        data=PlanData(
            status=PlanStatus.DRAFT,
            markdown_content="# Test Plan\n\nThis is a test plan.",
            description="A test plan for duplicate testing",
            tags=["test", "draft"]
        ),
        version=1,
        content_hash="abc123duplicate",
        created_at=current_time,
        updated_at=current_time
    )

    # Create the plan first time (should succeed)
    result1 = test_plan_service.create_new_plan(test_plan, "First creation")
    assert result1.success is True

    # Try to create the same plan again (should fail)
    result2 = test_plan_service.create_new_plan(test_plan, "Second creation")

    # Verify failure
    assert result2.success is False
    assert result2.plan_id == "test_duplicate_plan"
    assert result2.version == 1
    assert "already exists" in result2.error_message
    assert result2.error_type == "DuplicateError"

    # No cleanup needed - using separate test database


def test_create_new_plan_transaction_rollback(test_plan_service):
    """Test that database errors trigger transaction rollback"""
    # Create a test plan with invalid content hash to trigger constraint violation
    current_time = datetime.now()
    test_plan = Plan(
        id="test_rollback_plan",
        name="Test Rollback Plan",
        data=PlanData(
            status=PlanStatus.DRAFT,
            markdown_content="# Test Plan\n\nThis is a test plan.",
            description="A test plan for rollback testing",
            tags=["test", "draft"]
        ),
        version=1,
        content_hash="abc123rollback",
        created_at=current_time,
        updated_at=current_time
    )

    # First, create the plan normally
    result1 = test_plan_service.create_new_plan(test_plan, "First creation")
    assert result1.success is True

    # Now try to create a plan with the same ID but different content
    # This should trigger the duplicate ID error and rollback
    test_plan.content_hash = "different_hash"
    test_plan.data.description = "Modified description"

    result2 = test_plan_service.create_new_plan(test_plan, "Second creation")

    # Verify failure due to duplicate ID
    assert result2.success is False
    assert result2.plan_id == "test_rollback_plan"
    assert "already exists" in result2.error_message
    assert result2.error_type == "DuplicateError"

    # Verify the original plan is still there unchanged
    conn = test_plan_service.conn
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plans WHERE id = ?", (test_plan.id,))
    plan_row = cursor.fetchone()
    assert plan_row is not None
    assert plan_row['content_hash'] == "abc123rollback"  # Original hash

    # Verify only one history entry exists
    cursor.execute(
        "SELECT COUNT(*) FROM plan_history WHERE id = ?", (test_plan.id,))
    count = cursor.fetchone()[0]
    assert count == 1

    # Cleanup
    cursor.execute("DELETE FROM plans WHERE id = ?", (test_plan.id,))
    cursor.execute("DELETE FROM plan_history WHERE id = ?", (test_plan.id,))
    conn.commit()


def test_create_new_plan_version_history_details(test_plan_service):
    """Test that version history is created with correct details"""
    # Create a test plan
    current_time = datetime.now()
    test_plan = Plan(
        id="test_history_details_unique",
        name="Test History Details",
        data=PlanData(
            status=PlanStatus.APPROVED,
            markdown_content="# History Test\n\nTesting version history details.",
            description="Testing version history creation",
            tags=["test", "approved", "history"],
            metadata={"version": 1, "test_data": "history_test"}
        ),
        version=1,
        content_hash="history123test",
        created_at=current_time,
        updated_at=current_time
    )

    custom_summary = "Created via automated test with custom summary"

    # Create the plan
    result = test_plan_service.create_new_plan(test_plan, custom_summary)
    assert result.success is True

    # Verify detailed history entry
    conn = test_plan_service.conn
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, version, data, content_hash, created_at, archived_at, change_summary
        FROM plan_history WHERE id = ? AND version = ?
    """, (test_plan.id, 1))
    history_row = cursor.fetchone()

    assert history_row is not None
    assert history_row['id'] == test_plan.id
    assert history_row['version'] == 1
    assert history_row['content_hash'] == test_plan.content_hash
    assert history_row['change_summary'] == custom_summary
    assert history_row['created_at'] == current_time

    # Verify archived_at is after created_at (should be current time)
    archived_at = history_row['archived_at']
    assert archived_at >= current_time

    # Verify JSONB data is stored correctly
    # SQLite JSONB returns binary data, so we need to extract as text
    cursor.execute("""
        SELECT json_extract(data, '$.status') as status,
               json_extract(data, '$.description') as description,
               json_extract(data, '$.tags') as tags,
               json_extract(data, '$.metadata.test_data') as test_data
        FROM plan_history WHERE id = ? AND version = ?
    """, (test_plan.id, 1))
    json_data = cursor.fetchone()

    assert json_data['status'] == 'approved'
    assert json_data['description'] == 'Testing version history creation'
    assert 'history' in json_data['tags']
    assert json_data['test_data'] == 'history_test'

    # Cleanup
    cursor.execute("DELETE FROM plans WHERE id = ?", (test_plan.id,))
    cursor.execute("DELETE FROM plan_history WHERE id = ?", (test_plan.id,))
    conn.commit()
