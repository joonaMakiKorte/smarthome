from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_todos(mocker):
    mock_data = [
        {"id": "1", "content": "Test Task 1", "completed": False},
        {"id": "2", "content": "Test Task 2", "completed": True},
    ]
    mock_get_tasks = mocker.patch("app.services.todoist_service.get_all_tasks")
    mock_get_tasks.return_value = mock_data


    # Call API endpoint using TestClient
    response = client.get("/todos/")

    assert response.status_code == 200
    assert response.json() == mock_data
    mock_get_tasks.assert_called_once()