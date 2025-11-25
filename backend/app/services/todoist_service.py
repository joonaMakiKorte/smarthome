from app.schemas import TodoTask
from app.models import CompletedTask
from sqlmodel import Session, select, func
from typing import List
from todoist_api_python.api_async import TodoistAPIAsync
import os
from dotenv import load_dotenv

load_dotenv()

api = TodoistAPIAsync(os.getenv("TODOIST_API_KEY"))

async def get_all_tasks() -> List[TodoTask]:
    try:
        # Fetch all tasks with the label "Dashboard"
        # Returns a paginator to handle large number of tasks
        paginator = await api.get_tasks(label="Dashboard")
        all_tasks = []
        async for page in paginator:
            all_tasks.extend(page)

        # Map Todoist tasks to TodoTask schema
        mapped_tasks = [
            TodoTask(
                id=task.id,
                content=task.content,
                priority=task.priority
            )
            for task in all_tasks
        ]

        # Sort by priority (Descending: 4->1)
        mapped_tasks.sort(key=lambda x: x.priority, reverse=True)
        return mapped_tasks

    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return []
    
def get_completed_tasks(session: Session) -> List[CompletedTask]:
    """Fetch completed tasks from the local database."""
    statement = select(CompletedTask).order_by(CompletedTask.completed_at.desc())
    results = session.exec(statement).all()
    return results
    
async def complete_task(
        session: Session,
        task_id: str,
        content: str,
        priority: int
    ) -> bool:
    """Call Todoist API to complete a task and log it in the local database. Enforce 10 item limit."""
    try:
        success = await api.complete_task(task_id)
        if not success:
            return False
        
        completed_task = CompletedTask(
            id=task_id,
            content=content,
            priority=priority
        )
        session.add(completed_task)
        session.commit()

        count = session.exec(select(func.count()).select_from(CompletedTask)).one()
        if count > 10:
            oldest_task = session.exec(
                select(CompletedTask).order_by(CompletedTask.completed_at)
            ).first()
            if oldest_task:
                session.delete(oldest_task)
                session.commit()
        
        return True
    
    except Exception as e:
        print(f"Error completing task {task_id}: {e}")
        return False
    
async def reopen_task(session: Session, task_id: str) -> bool:
    """Call Todoist API to reopen a task and remove it from the local database."""
    try:
        success = await api.uncomplete_task(task_id)
        if not success:
            return False
        
        task_in_db = session.get(CompletedTask, task_id)
        if task_in_db:
            session.delete(task_in_db)
            session.commit()

        return True
    
    except Exception as e:
        print(f"Error reopening task {task_id}: {e}")
        return False
    