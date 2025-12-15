import asyncio
from app.services import todoist_service, electricity_service, stocks_service
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
    await _create_stocks_scheduler()
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

MAX_RETRIES = 30
RETRY_DELAY = 60 # 60 sec delay between retries
async def _electricity_job_wrapper():
    """
    Try to fetch electricity prices.
    Retries in a loop until fresh data is present or is out of tries."""
    for _ in range(MAX_RETRIES):
        with Session(engine) as session:
            try:
                await electricity_service.fetch_and_store_electricity_prices(session)

                if not electricity_service.check_if_fetch_needed(session):
                    # If tomorrows data is present -> break
                    return

            except Exception as e:
                print(f"Error in electricity job: {e}")

        await asyncio.sleep(RETRY_DELAY)

TZ_HELSINKI = ZoneInfo("Europe/Helsinki")
async def _create_electricity_scheduler():
    """Fetches electricity price at 14:02 daily + at initial launch"""
    # Daily Recurrent Job
    scheduler.add_job(
        _electricity_job_wrapper,
        trigger=CronTrigger(hour=14, minute=2, timezone=TZ_HELSINKI),
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

# --- Stocks ---

TZ_NY = ZoneInfo("America/New_York")
async def _stocks_prune_wrapper():
    """Wraps the synchronous prune function in a thread to avoid blocking the loop."""
    with Session(engine) as session:
        try:
            # Run the sync function in a threadpool
            await asyncio.to_thread(stocks_service.prune_db_history, session)
        except Exception as e:
            print(f"Error in stocks prune job: {e}")

async def _create_stocks_scheduler():
    """Prunes stock history at 9:30 NY time daily + at initial launch"""
    # Daily Recurrent Job (9:30 AM NY)
    scheduler.add_job(
        _stocks_prune_wrapper,
        trigger=CronTrigger(hour=9, minute=30, timezone=TZ_NY),
        id="stocks_daily_prune",
        replace_existing=True
    )

    # Startup Job
    scheduler.add_job(
        _stocks_prune_wrapper,
        trigger='date',
        id="stocks_startup_prune",
        replace_existing=True
    )
