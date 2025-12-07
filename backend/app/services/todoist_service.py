import os
from dotenv import load_dotenv
from app.schemas import TodoTask
from app.models import CompletedTask
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime
from todoist_api_python.api_async import TodoistAPIAsync
import asyncio
from fastapi.concurrency import run_in_threadpool

# API config
load_dotenv()
API = TodoistAPIAsync(os.getenv("TODOIST_API_KEY"))

class TaskCache:
    """Single Source of Truth Cache maintaining a simple list of tasks in memory"""
    def __init__(self):
        self._cache: List[TodoTask] = []
        self._last_updated: Optional[datetime] = None
        self._lock = asyncio.Lock() # Prevent read/write conflicts

    @property
    def cache(self) -> List[TodoTask]:
        return self._cache

    def is_empty(self) -> bool:
        return not self._cache and not self._last_updated
    
    async def replace_cache(self, tasks: List[TodoTask]):
        async with self._lock:
            self._cache = tasks
            self._last_updated = datetime.now()

    async def remove_from_cache(self, task_id: str):
        """Updates memory cache by removing the task requested by id."""
        async with self._lock:
            self._cache = [t for t in self._cache if t.id != task_id]
    
# Init global cache
task_cache = TaskCache()


# --- Public functions ---

async def get_tasks() -> List[TodoTask]:
    """Return cached tasts. Handles fetching if empty."""
    if task_cache.is_empty():
        await refresh_tasks()
    return task_cache.cache

async def refresh_tasks():
    """Fetches fresh data from Todoist and handles caching."""
    # Fetch all tasks with the label "Dashboard"
    # Returns a paginator to handle large number of tasks
    paginator = await API.get_tasks(label="Dashboard")
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

    # Cache
    await task_cache.replace_cache(mapped_tasks)
    
async def complete_task(session: Session, task_id: str, content: str, priority: int) -> bool:
    """Complete task with Write-Through caching."""
    success = await API.complete_task(task_id)
    if not success:
        return False
    
    # Update to db
    await run_in_threadpool(_log_completion_to_db, session, task_id, content, priority)
    
    # Update memory cache
    await task_cache.remove_from_cache(task_id)

    return True
    
async def reopen_task(session: Session, task_id: str) -> bool:
    """Call Todoist API to reopen a task and remove it from the local database."""
    success = await API.uncomplete_task(task_id)
    if not success:
        return False
    
    # Remove from local db history
    await run_in_threadpool(_remove_from_db, session, task_id)

    # Immediate refresh
    await refresh_tasks()

    return True
    
def fetch_completed_tasks(session: Session) -> List[CompletedTask]:
    """Fetch completed tasks from the local database."""
    statement = select(CompletedTask).order_by(CompletedTask.completed_at.desc())
    results = session.exec(statement).all()
    return results


# --- DB helpers ---

def _log_completion_to_db(session: Session, task_id: str, content: str, priority: int):
    """Write completed task to db. Enforces 10 item limit."""
    try:
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
    
    except Exception as e:
        session.rollback()
        print(f"Database error during todo task completion: {e}")
        raise e 

def _remove_from_db(session: Session, task_id: str):
    """Delete requested task from db."""
    try:
        task_in_db = session.get(CompletedTask, task_id)
        if task_in_db:
            session.delete(task_in_db)
            session.commit()
    
    except Exception as e:
        session.rollback()
        print(f"Database error during todo task reopening: {e}")
        raise e 