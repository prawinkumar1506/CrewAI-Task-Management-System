# tests/test_reassignment.py
import pytest
from datetime import datetime, timedelta
from app.models.sample_data import SampleUser, SampleUserTask
from app.agents.task_reassign import reassign_task




# tests/test_reassignment.py
import pytest
from datetime import datetime, timedelta
from app.models.sample_data import SampleUser, SampleUserTask
from app.agents.task_reassign import reassign_task

@pytest.fixture(autouse=True)
def clean_database():
    """Clean database before each test"""
    SampleUser.objects().delete()
    SampleUserTask.objects().delete()

def test_auto_reassignment():
    # Create test user
    user = SampleUser(
        user_id="U_AUTO1",
        username="Auto User",
        skills={"python": 8},
        max_concurrent_tasks=3,
        availability_status="available"
    ).save()

    # Create test task
    task = SampleUserTask(
        task_id="T_AUTO1",
        name="Python Migration",
        required_skills={"python": 7},
        status="in_progress"
    ).save()

    # Perform auto reassignment
    result = reassign_task(task.task_id)
    
    # Verify results
    assert result['status'] == 'success'
    assert result['user_id'] == user.user_id

def test_successful_reassignment():
    # Setup test data
    user1 = SampleUser(
        user_id="U_TEST1",
        username="Test User 1",
        skills={"python": 8, "security": 7},
        max_concurrent_tasks=3,
        availability_status="available"
    ).save()

    user2 = SampleUser(
        user_id="U_TEST2",
        username="Test User 2",
        skills={"python": 9, "security": 8},
        max_concurrent_tasks=3,
        availability_status="available"
    ).save()

    task = SampleUserTask(
        task_id="T_TEST1",
        name="Security Audit",
        required_skills={"python": 7, "security": 6},
        status="in_progress",
        user_id=user1.user_id
    ).save()

    # Verify initial state
    assert user1.current_ongoing_tasks == 0
    assert user2.current_ongoing_tasks == 0
    assert task.user_id == user1.user_id

    # Perform reassignment
    result = reassign_task(task.task_id, force_user_id=user2.user_id)
    
    # Verify results
    assert result['status'] == 'success'
    assert result['user_id'] == user2.user_id
    
    # Refresh objects from DB
    user1.reload()
    user2.reload()
    task.reload()
    
    assert user1.current_ongoing_tasks == 0
    assert user2.current_ongoing_tasks == 1
    assert task.user_id == user2.user_id
    assert task.reassigned_count == 1


def test_reassignment_validation():
    # Setup test data
    busy_user = SampleUser(
        user_id="U_BUSY",
        username="Busy User",
        skills={"python": 9},
        max_concurrent_tasks=1,
        availability_status="available",
        current_ongoing_tasks=1
    ).save()

    task = SampleUserTask(
        task_id="T_VALID1",
        name="Validation Test",
        required_skills={"python": 7},
        status="in_progress"
    ).save()

    # Attempt reassignment to busy user
    result = reassign_task(task.task_id, force_user_id=busy_user.user_id)
    
    assert "error" in result
    assert "max capacity" in result['error'].lower()
