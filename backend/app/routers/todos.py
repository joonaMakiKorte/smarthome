from typing import List
from fastapi import APIRouter, HTTPException
from app.services import todoist_service
from app.schemas import TodoTask

router = APIRouter()

@router.get("/todos", response_model=List[TodoTask])
def read_todos():
    return todoist_service.get_all_tasks()

@router.post("/todos/{task_id}/complete")
def complete_todo(task_id: str):
    success = todoist_service.complete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "Task completed"}
