from fastapi.testclient import TestClient
from app.main import app
from app.models import CompletedTask
from app.database import get_session
from datetime import datetime

client = TestClient(app)

def test_read_todos(mocker):
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


def test_read_completed_todos(mocker):
    mock_session = mocker.MagicMock()

    mock_data = [
        CompletedTask(id="1", content="Completed Task 1", priority=2, completed_at=datetime.utcnow()),
        CompletedTask(id="2", content="Completed Task 2", priority=1, completed_at=datetime.utcnow())
    ]
    # Mock the database query chain
    mock_session.exec.return_value.all.return_value = mock_data

    # Override the get_session dependency to use the mock session
    app.dependency_overrides[get_session] = lambda: mock_session

    response = client.get("/todos/completed")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["id"] == "1"

    # Clean up dependency override
    app.dependency_overrides = {}


def test_complete_todo_success(mocker):
    mock_complete_task = mocker.patch("app.services.todoist_service.complete_task")
    mock_complete_task.return_value = True

    mock_session = mocker.MagicMock()
    mock_session.exec.return_value.one.return_value = 5 # Simulate 5 completed tasks in DB to not trigger deletion

    app.dependency_overrides[get_session] = lambda: mock_session

    task_id = "1"
    params = {
        "task_content": "Test Task",
        "priority": 3
    }

    response = client.post(f"/todos/{task_id}/complete", params=params)

    assert response.status_code == 200
    assert response.json() == {"status": "Task completed"}

    mock_complete_task.assert_called_once_with(task_id)

    # Verify that the completed task was added to the session and committed
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called()

    # Clean up dependency override
    app.dependency_overrides = {}


def test_reopen_todo_success(mocker):
    mock_reopen_task = mocker.patch("app.services.todoist_service.reopen_task")
    mock_reopen_task.return_value = True

    mock_session = mocker.MagicMock()

    fake_completed_task = CompletedTask(id="1", content="Completed Task", priority=2, completed_at=datetime.utcnow())
    mock_session.get.return_value = fake_completed_task

    app.dependency_overrides[get_session] = lambda: mock_session

    task_id = "123"
    response = client.post(f"/todos/{task_id}/reopen")

    assert response.status_code == 200
    assert response.json() == {"status": "Task reopened"}

    mock_reopen_task.assert_called_once_with(task_id)

    # Verify that the completed task was deleted from the session and committed
    mock_session.delete.assert_called_once_with(fake_completed_task)
    mock_session.commit.assert_called()

    # Clean up dependency override
    app.dependency_overrides = {}