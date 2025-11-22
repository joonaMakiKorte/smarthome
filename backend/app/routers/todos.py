from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select, func
from app.database import get_session
from app.services import todoist_service
from app.schemas import TodoTask
from app.models import CompletedTask

router = APIRouter()

@router.get("/todos", response_model=List[TodoTask])
def read_todos():
    """Fetch all active todos from Todoist."""
    return todoist_service.get_all_tasks()

@router.get("/todos/completed", response_model=List[CompletedTask])
def read_completed_todos(session: Session = Depends(get_session)):
    """Fetch the last 10 completed todos from the local database."""
    statement = select(CompletedTask).order_by(CompletedTask.completed_at.desc())
    results = session.exec(statement).all()
    return results

@router.post("/todos/{task_id}/complete")
def complete_todo(
    task_id: str,
    task_content: str,
    priority: int,
    session: Session = Depends(get_session)
):
    """Complete a todo task in Todoist and log it in the local database."""
    success = todoist_service.complete_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Could not complete task in Todoist")

    completed_task = CompletedTask(
        id=task_id,
        content=task_content,
        priority=priority
    )
    session.add(completed_task)
    session.commit()
    
    # Enforce 10 item limit
    count = session.exec(select(func.count()).select_from(CompletedTask)).one()
    if count > 10:
        # Find and delete the oldest entry
        oldest_task = session.exec(
            select(CompletedTask).order_by(CompletedTask.completed_at)
        ).first()
        if oldest_task:
            session.delete(oldest_task)
            session.commit()    

    return {"status": "Task completed"}

@router.post("/todos/{task_id}/reopen")
def reopen_todo(
    task_id: str,
    session: Session = Depends(get_session)
):
    """Reopen a completed todo task in Todoist and remove it from the local database."""
    success = todoist_service.reopen_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Could not reopen task in Todoist")

    completed_task = session.get(CompletedTask, task_id)
    if completed_task:
        session.delete(completed_task)
        session.commit()

    return {"status": "Task reopened"}
