from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select, func
from app.database import get_session
from app.services import todoist_service
from app.schemas import TodoTask
from app.models import CompletedTask
from app.utils import handle_upstream_errors

router = APIRouter()

@router.get("/todos", response_model=List[TodoTask])
async def read_todos():
    """Fetch all active todos from Todoist."""
    async with handle_upstream_errors("Todoist"):
        return await todoist_service.fetch_all_tasks()

@router.get("/todos/completed", response_model=List[CompletedTask])
def read_completed_todos(session: Session = Depends(get_session)):
    """Fetch the last 10 completed todos from the local database."""
    return todoist_service.fetch_completed_tasks(session)

@router.post("/todos/{task_id}/complete")
async def complete_todo(task_id: str, task_content: str, priority: int, session: Session = Depends(get_session)):
    """Complete a todo task in Todoist and log it in the local database."""
    async with handle_upstream_errors("Todoist"):
        success = await todoist_service.complete_task(session, task_id, task_content, priority)
        if not success:
            print("Error completing task in Todoist")
            raise HTTPException(
                status_code=400,
                detail="Could not complete task in Todoist")
        return {"status": "Task completed"}

@router.post("/todos/{task_id}/reopen")
async def reopen_todo(task_id: str, session: Session = Depends(get_session)):
    """Reopen a completed todo task in Todoist and remove it from the local database."""
    async with handle_upstream_errors("Todoist"):
        success = await todoist_service.reopen_task(session, task_id)
    if not success:
        print("Error reopening task in Todoist")
        raise HTTPException(
            status_code=400,
            detail="Could not reopen task in Todoist")
    return {"status": "Task reopened"}
