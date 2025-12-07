import httpx
from app.models import ElectricityPrice
from app.schemas import ElectricityPriceInterval
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select, func, delete
from typing import Literal, List
from fastapi.concurrency import run_in_threadpool

URL = "https://api.porssisahko.net/v2/latest-prices.json"

async def fetch_and_store_electricity_prices(session: Session):
    """
    Fetches electricity prices from API and saves to DB (Upsert).
    Handles deletion of electricity data older than 10 days.
    """
    # Check if we already have the latest data
    should_fetch = await run_in_threadpool(_check_if_fetch_needed, session)
    if not should_fetch:
        return

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(URL)
        response.raise_for_status()
        data = response.json()

    # Write to db
    await run_in_threadpool(_batch_upsert_and_delete, session, data)

def _check_if_fetch_needed(session: Session) -> bool:
    # Get the latest timestamp in db
    statement = select(func.max(ElectricityPrice.start_time))
    latest_ts = session.exec(statement).first()

    if not latest_ts:
        # DB is empty
        return True

    # Get tomorrows date
    now = datetime.now(tz=timezone.utc)
    tomorrow_date = now.date() + timedelta(days=1)

    # If latest timestamp found is tomorrow, it means we have the full day
    # (porssisahko.net returns full day data at once)
    latest_date = latest_ts.date()

    return latest_date < tomorrow_date 
    
def _batch_upsert_and_delete(session: Session, api_data):
    """Write electricity prices to db and cleanup old data"""
    # Write to db
    try:
        for entry in api_data["prices"]:
            session.merge(ElectricityPrice(
                start_time=datetime.fromisoformat(entry["startDate"].replace("Z", "+00:00")),
                end_time=datetime.fromisoformat(entry["endDate"].replace("Z", "+00:00")),
                price=entry["price"] if entry["price"] >= 0 else 0.0
            ))

        # Old data cleanup
        cutoff_time = datetime.now(tz=timezone.utc) - timedelta(days=10)
        statement = delete(ElectricityPrice).where(ElectricityPrice.start_time < cutoff_time)
        session.exec(statement)

        session.commit()

    except Exception as e:
        # Rollback to ensure no partial data is left
        session.rollback()
        print(f"Database error during electricity update: {e}")
        raise e 


def get_electricity_prices(session: Session, mode: Literal["15min", "1h"] = "15min") -> List[ElectricityPriceInterval]:
    """
    Fetches prices for Today (00:00) through Tomorrow (23:59)
    Default 15min intervals, aggregate to 1h average if requested.
    """
    now = datetime.now(tz=timezone.utc)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_window = start_of_today + timedelta(days=2)

    # Query for electricity prices
    statement = (
        select(ElectricityPrice)
        .where(ElectricityPrice.start_time >= start_of_today)
        .where(ElectricityPrice.start_time < end_of_window)
        .order_by(ElectricityPrice.start_time)
    )
    results = session.exec(statement).all()

    # Return results immediately if is 15min mode
    if mode == "15min":
        return [ElectricityPriceInterval(
            time=p.start_time,
            price=p.price
        ) for p in results
    ]

    if mode == "1h":
        hourly_data = []

        # Group prices into dictionary, keyed by hour
        grouped = {}
        for row in results:
            # Truncate minutes to 00
            hour_key = row.start_time.replace(minute=0, second=0, microsecond=0)
            if hour_key not in grouped:
                grouped[hour_key] = []
            grouped[hour_key].append(row.price)

        # Get averages
        for start_time, prices in grouped.items():
            avg_price = sum(prices) / len(prices)

            hourly_data.append(ElectricityPriceInterval(
                time=start_time,
                price=avg_price
            ))
        return hourly_data
    

def calculate_10_day_avg(session: Session) -> float:
    """Get the average price from 10 days."""
    now = datetime.now(tz=timezone.utc)
    ten_days_ago = now - timedelta(days=10)

    # Aggregation Query
    statement = (
        select(func.avg(ElectricityPrice.price))
        .where(ElectricityPrice.start_time >= ten_days_ago)
        .where(ElectricityPrice.start_time < now)
    )
    avg_price = session.exec(statement).first()
    return avg_price if avg_price is not None else 0.0
    