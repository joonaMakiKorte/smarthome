from app.schemas import TodoTask
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
    
async def complete_task(task_id: str):
    try:
        return await api.complete_task(task_id)
    except Exception as e:
        print(f"Error completing task {task_id}: {e}")
        return False
    
async def reopen_task(task_id: str):
    try:
        return await api.uncomplete_task(task_id)
    except Exception as e:
        print(f"Error reopening task {task_id}: {e}")
        return False
    