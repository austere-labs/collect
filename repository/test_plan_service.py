import pytest
from repository.database import SQLite3Database
from repository.plan_service import PlanService


@pytest.fixture
def test_plan_service():
    db_path = "data/plans.db"  # Fixed path
    db = SQLite3Database(db_path)
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
    # Clear database first to ensure clean test
    conn = test_plan_service.conn
    cursor = conn.cursor()
    cursor.execute("DELETE FROM plans")
    conn.commit()

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
    # Clear database first
    conn = test_plan_service.conn
    cursor = conn.cursor()
    cursor.execute("DELETE FROM plans")
    conn.commit()

    # Test the complete sync workflow
    result = test_plan_service.sync_plans()

    # Get expected count from the actual result
    expected_count = result.loaded_count

    # Verify the sync worked
    assert result.loaded_count > 0  # Should load some plans
    assert result.error_count == 0

    # Verify plans are in database
    cursor.execute("SELECT COUNT(*) FROM plans")
    count = cursor.fetchone()[0]
    assert count == expected_count

    print(f"✅ Sync completed: {result.loaded_count} plans synced")


def test_database_connection(test_plan_service):
    conn = test_plan_service.conn
    cursor = conn.cursor()
    # Test: Try a simple insert/select
    cursor.execute("""
        INSERT INTO plans (id, name, data, content_hash)
        VALUES ('test-1', 'Test Plan', '{"test": true}', 'hash123')
    """)

    cursor.execute("SELECT name FROM plans WHERE id = 'test-1'")
    result = cursor.fetchone()
    assert result[0] == 'Test Plan'

    # Rollback to keep test database clean
    conn.rollback()
