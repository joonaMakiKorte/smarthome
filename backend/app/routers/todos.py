from fastapi import APIRouter, HTTPException
from app.services import todoist_service
from pydantic import BaseModel

router = APIRouter()

@router.get("/todos")
def read_todos():
    return todoist_service.get_all_tasks()

@router.post("/todos/{task_id}/complete")
def complete_todo(task_id: str):
    success = todoist_service.complete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "Task completed"}
