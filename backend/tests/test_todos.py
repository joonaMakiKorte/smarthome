from app.main import app
from app.models import CompletedTask
from app.database import get_session
from datetime import datetime


def test_read_todos(client, mocker):
    """Test fetching current todos"""
    mock_data = [
        {"id": "1", "content": "Test Task 1", "priority": 3},
        {"id": "2", "content": "Test Task 2", "priority": 4},
    ]
    mock_get_tasks = mocker.patch("app.services.todoist_service.get_all_tasks")
    mock_get_tasks.return_value = mock_data


    # Call API endpoint using TestClient
    response = client.get("/todos/")

    assert response.status_code == 200
    assert response.json() == mock_data
    mock_get_tasks.assert_called_once()


def test_read_completed_todos(client, session):
    """Test fetching history."""
    task1 = CompletedTask(id="1", content="Completed Task 1", priority=2, completed_at=datetime.utcnow())
    task2 = CompletedTask(id="2", content="Completed Task 2", priority=1, completed_at=datetime.utcnow())
    session.add(task1)
    session.add(task2)
    session.commit()

    response = client.get("/todos/completed")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["id"] == "2"


def test_complete_todo_success(client, session, mocker):
    """Test completing a todo successfully."""
    mock_complete_task = mocker.patch("app.services.todoist_service.complete_task")
    mock_complete_task.return_value = True

    task_id = "1"
    params = {
        "task_content": "Test Task",
        "priority": 3
    }

    response = client.post(f"/todos/{task_id}/complete", params=params)

    assert response.status_code == 200
    assert response.json() == {"status": "Task completed"}

    saved_task = session.get(CompletedTask, task_id)
    assert saved_task is not None
    assert saved_task.content == "Test Task"

    mock_complete_task.assert_called_once_with(task_id)


def test_reopen_todo_success(client, session, mocker):
    """Test reopening a completed todo successfully."""
    task_id = "999"
    existing_task = CompletedTask(id=task_id, content="Reopen Me", priority=1)
    session.add(existing_task)
    session.commit()

    mock_reopen_task = mocker.patch("app.services.todoist_service.reopen_task")
    mock_reopen_task.return_value = True

    response = client.post(f"/todos/{task_id}/reopen")

    assert response.status_code == 200
    assert response.json() == {"status": "Task reopened"}

    # Verify task is removed from local DB
    reopened_task = session.get(CompletedTask, task_id)
    assert reopened_task is None

    mock_reopen_task.assert_called_once_with(task_id)
