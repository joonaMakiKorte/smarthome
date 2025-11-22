from app.schemas import TodoTask
from todoist_api_python.api import TodoistAPI
import os
from dotenv import load_dotenv

load_dotenv()

api = TodoistAPI(os.getenv("TODOIST_API_KEY"))

def get_all_tasks():
    try:
        # Fetch all tasks with the label "Dashboard"
        # Returns a paginator to handle large number of tasks
        paginator = api.get_tasks(label="Dashboard")
        all_tasks = []
        for page in paginator:
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
    
def complete_task(task_id: str):
    try:
        return api.complete_task(task_id)
    except Exception as e:
        print(f"Error completing task {task_id}: {e}")
        return False
    
def reopen_task(task_id: str):
    try:
        return api.uncomplete_task(task_id)
    except Exception as e:
        print(f"Error reopening task {task_id}: {e}")
        return False
    