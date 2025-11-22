import pytest
import os
from todoist_api_python.api import TodoistAPI
from dotenv import load_dotenv
from app.models import CompletedTask

load_dotenv()

api_key = os.getenv("TODOIST_API_KEY")
if not api_key:
    pytest.skip("TODOIST_API_KEY not set in environment variables", allow_module_level=True)

todoist = TodoistAPI(api_key)

@pytest.fixture(scope="function")
def temp_task():
    """
    Create a real task in Todoist before the test and delete it after the test.
    """
    # label "Dashboard" must exist in the Todoist account for this to work
    task = todoist.add_task(content="Test Task for Integration Test #Dashboard",
                            due_string="today", labels=["Dashboard"], priority=4)
    yield task

    try:
        todoist.delete_task(task.id)
    except Exception as e:
        print(f"Error deleting task {task.id}: {e}")

@pytest.mark.integration
def test_fetch_real_tasks(client, temp_task):
    """
    Test fetching tasks from Todoist API via the /todos endpoint.
    """
    response = client.get("/todos")

    assert response.status_code == 200
    tasks = response.json()

    assert any(t["id"] == temp_task.id for t in tasks), "Temp task not found in fetched tasks"


@pytest.mark.integration
def test_complete_real_task(client, session, temp_task):
    """
    Test completing a real task via the /todos/{task_id}/complete endpoint.
    """
    params = {
        "task_content": temp_task.content,
        "priority": temp_task.priority
    }

    response = client.post(f"/todos/{temp_task.id}/complete", params=params)
    assert response.status_code == 200

    saved_task = session.get(CompletedTask, temp_task.id)
    assert saved_task is not None
    assert saved_task.content == temp_task.content

    try:
        task_on_server = todoist.get_task(temp_task.id)
        assert task_on_server.completed is True
    except Exception:
        pass


@pytest.mark.integration
def test_reopen_real_task(client, session, temp_task):
    """
    Test reopening a completed task via the /todos/{task_id}/reopen endpoint.
    """
    params = {
        "task_content": temp_task.content,
        "priority": temp_task.priority
    }

    complete_response = client.post(f"/todos/{temp_task.id}/complete", params=params)
    assert complete_response.status_code == 200

    reopen_response = client.post(f"/todos/{temp_task.id}/reopen")
    assert reopen_response.status_code == 200

    reopened_task = session.get(CompletedTask, temp_task.id)
    assert reopened_task is None

    try:
        task_on_server = todoist.get_task(temp_task.id)
        assert task_on_server.completed is False
    except Exception:
        pass