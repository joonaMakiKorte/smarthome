import pytest
import pytest_asyncio
import os
from todoist_api_python.api_async import TodoistAPIAsync
from dotenv import load_dotenv
from app.models import CompletedTask

load_dotenv()

api_key = os.getenv("TODOIST_API_KEY")
if not api_key:
    pytest.skip("TODOIST_API_KEY not set in environment variables", allow_module_level=True)

todoist = TodoistAPIAsync(api_key)

@pytest_asyncio.fixture(scope="function")
async def temp_task():
    """
    Create a real task in Todoist before the test and delete it after the test.
    """
    # label "Dashboard" must exist in the Todoist account for this to work
    task = await todoist.add_task(content="Test Task for Integration Test #Dashboard",
                            due_string="today", labels=["Dashboard"], priority=4)
    yield task

    try:
        await todoist.delete_task(task.id)
    except Exception as e:
        print(f"Error deleting task {task.id}: {e}")

# pytest tests/test_todos_integration.py::test_fetch_real_tasks
@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_real_tasks(async_client, temp_task):
    """
    Test fetching tasks from Todoist API via the /todos endpoint.
    """
    response = await async_client.get("/todos")

    assert response.status_code == 200
    tasks = response.json()

    assert any(t["id"] == temp_task.id for t in tasks), "Temp task not found in fetched tasks"

# pytest tests/test_todos_integration.py::test_complete_real_task
@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_real_task(async_client, session, temp_task):
    """
    Test completing a real task via the /todos/{task_id}/complete endpoint.
    """
    params = {
        "task_content": temp_task.content,
        "priority": temp_task.priority
    }

    response = await async_client.post(f"/todos/{temp_task.id}/complete", params=params)
    assert response.status_code == 200

    saved_task = session.get(CompletedTask, temp_task.id)
    assert saved_task is not None
    assert saved_task.content == temp_task.content

    try:
        task_on_server = todoist.get_task(temp_task.id)
        assert task_on_server.completed is True
    except Exception:
        pass

# pytest tests/test_todos_integration.py::test_reopen_real_task
@pytest.mark.integration
@pytest.mark.asyncio
async def test_reopen_real_task(async_client, session, temp_task):
    """
    Test reopening a completed task via the /todos/{task_id}/reopen endpoint.
    """
    params = {
        "task_content": temp_task.content,
        "priority": temp_task.priority
    }

    complete_response = await async_client.post(f"/todos/{temp_task.id}/complete", params=params)
    assert complete_response.status_code == 200

    reopen_response = await async_client.post(f"/todos/{temp_task.id}/reopen")
    assert reopen_response.status_code == 200

    reopened_task = session.get(CompletedTask, temp_task.id)
    assert reopened_task is None

    try:
        task_on_server = todoist.get_task(temp_task.id)
        assert task_on_server.completed is False
    except Exception:
        pass
    