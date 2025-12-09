import asyncio
from app.services import todoist_service, openweather_service

async def start_periodic_services():
    """Launches all background loops as independent async tasks."""
    asyncio.create_task(_run_todoist_poller())
    
async def _run_todoist_poller():
    """Polls Todoist every 10 seconds."""
    while True:
        try:
            await todoist_service.refresh_tasks()
        except Exception as e:
            print(f"Error in todoist poller: {e}")
        
        await asyncio.sleep(10)
