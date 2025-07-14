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
    assert len(plans) == 5  # Should have 5 plans from our test data

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
