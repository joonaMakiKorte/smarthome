from todoist_api_python import TodoistAPI
import os
from dotenv import load_dotenv

load_dotenv()

api = TodoistAPI(os.getenv("TODOIST_API_KEY"))

def get_dashboard_tasks():
    try:
        # Fetch all tasks with the label "Dashboard" or due today
        tasks = api.get_tasks(filter="today | #Dashboard")
        return [
            {"id": task.id, "content": task.content, "due": task.due.date, "is_completed": task.completed}
            for task in tasks
        ]
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return []
    
def complete_task(task_id: str):
    try:
        is_success = api.close_task(task_id)
        return is_success
    except Exception as e:
        print(f"Error completing task {task_id}: {e}")
        return False