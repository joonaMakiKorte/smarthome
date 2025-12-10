import asyncio
from app.services import todoist_service, electricity_service
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
from app.database import engine
from sqlmodel import Session

# Global scheduler
scheduler = AsyncIOScheduler()

async def start_periodic_services():
    """
    Launches all background loops as independent async tasks.
    Adds scheduler tasks and starts the scheduler
    """
    # Run asyncio tasks
    asyncio.create_task(_run_todoist_poller())

    # Create and run schedulers
    await _create_electricity_scheduler()
    scheduler.start()

# --- Todoist ---
    
async def _run_todoist_poller():
    """Polls Todoist every 10 seconds."""
    while True:
        try:
            await todoist_service.refresh_tasks()
        except Exception as e:
            print(f"Error in todoist poller: {e}")
        
        await asyncio.sleep(10)

# --- Electricity ---

async def _electricity_job_wrapper():
    with Session(engine) as session:
        try:
            await electricity_service.fetch_and_store_electricity_prices(session)
        except Exception as e:
            print(f"Error in electricity job: {e}")

TZ_HELSINKI = ZoneInfo("Europe/Helsinki")
async def _create_electricity_scheduler():
    """Fetches electricity price at 14:00 daily + at initial launch"""
    # Daily Recurrent Job
    scheduler.add_job(
        _electricity_job_wrapper,
        trigger=CronTrigger(hour=14, minute=0, timezone=TZ_HELSINKI),
        id="electricity_daily_fetch",
        replace_existing=True
    )

    # Startup Job
    scheduler.add_job(
        _electricity_job_wrapper,
        trigger='date',
        id="electricity_startup_fetch",
        replace_existing=True
    )
