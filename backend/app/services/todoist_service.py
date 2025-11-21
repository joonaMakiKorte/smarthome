from app.schemas import TodoTask
from todoist_api_python.api import TodoistAPI
import os
from dotenv import load_dotenv

load_dotenv()

api = TodoistAPI(os.getenv("TODOIST_API_KEY"))

def get_all_tasks():
    try:
        # Fetch all tasks with the label "#Dashboard"
        # Returns a paginator to handle large number of tasks
        paginator = api.get_tasks()
        all_tasks = []
        for page in paginator:
            all_tasks.extend(page)

        # Map Todoist tasks to TodoTask schema
        return [
            TodoTask(
                id=task.id,
                content=task.content,
                completed=task.is_completed
            )
            for task in all_tasks
        ]
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return []
    
def complete_task(task_id: str):
    try:
        is_success = api.complete_task(task_id)
        return is_success
    except Exception as e:
        print(f"Error completing task {task_id}: {e}")
        return False
    