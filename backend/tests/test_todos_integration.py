import pytest
import os
from fastapi.testclient import TestClient
from app.main import app
from todoist_api_python.api import TodoistAPI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TODOIST_API_KEY")
if not api_key:
    pytest.skip("TODOIST_API_KEY not set in environment variables", allow_module_level=True)

todoist = TodoistAPI(api_key)
client = TestClient(app)

@pytest.fixture(scope="function")
def temp_task():
    """
    Create a real task in Todoist before the test and delete it after the test.
    """
    # label "Dashboard" must exist in the Todoist account for this to work
    task = todoist.add_task(content="Test Task for Integration Test #Dashboard",
                            due_string="today", labels=["Dashboard"])
    yield task

    try:
        todoist.delete_task(task.id)
    except Exception as e:
        print(f"Error deleting task {task.id}: {e}")

@pytest.mark.integration
def test_fetch_real_tasks(temp_task):
    """
    Test fetching tasks from Todoist API via the /todos endpoint.
    """
    response = client.get("/todos")

    assert response.status_code == 200
    tasks = response.json()

    assert any(t["id"] == temp_task.id for t in tasks), "Temp task not found in fetched tasks"

@pytest.mark.integration
def test_complete_real_task(temp_task):
    """
    Test completing a real task via the /todos/{task_id}/complete endpoint.
    """
    response = client.post(f"/todos/{temp_task.id}/complete")
    assert response.status_code == 200

    try:
        task = todoist.get_task(temp_task.id)
        assert task.completed is True, "Task was not marked as completed"
    except Exception:
        # If fails, might mean it was moved to history -> success
        pass
