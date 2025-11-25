import httpx
from app.models import ElectricityPrice
from app.database import get_session
from zoneinfo import ZoneInfo
from datetime import datetime
from sqlmodel import Session
from fastapi import Depends

url = "https://api.porssisahko.net/v2/latest-prices.json"
FINLAND_TZ = ZoneInfo("Europe/Helsinki")

def convert_to_helsinki_time(utc_datetime: datetime) -> datetime:
    """Converts a UTC datetime to Helsinki time."""
    # Ensure the input datetime is timezone-aware
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=ZoneInfo("UTC"))
    return utc_datetime.astimezone(FINLAND_TZ)

async def fetch_and_store_electricity_prices(session: Session = Depends(get_session)):
    """Fetches electricity prices from API and saves to DB (Upsert)."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        for entry in data["prices"]:
            start = datetime.fromisoformat(entry["startDate"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(entry["endDate"].replace("Z", "+00:00"))

            session.merge(ElectricityPrice(
                start_time=convert_to_helsinki_time(start),
                end_time=convert_to_helsinki_time(end),
                price=entry["price"]
            ))
        session.commit()

    except Exception as e:
        print(f"Error fetching or storing electricity prices: {e}")