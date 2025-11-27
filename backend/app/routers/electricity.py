from fastapi import APIRouter, Depends, Query
from app.database import get_session
from sqlmodel import Session
from app.services.electricity_service import fetch_and_store_electricity_prices, get_electricity_prices, calculate_10_day_avg
from typing import List
from app.schemas import ElectricityPriceInterval, AvgElectricityPrice
from datetime import datetime, timezone, timedelta

router = APIRouter()  

@router.post("/electricity/refresh")
async def refresh_electricity_prices(session: Session = Depends(get_session)):
    """Endpoint to refresh electricity prices from external API."""
    await fetch_and_store_electricity_prices(session)
    return {"status": "Electricity prices refreshed"}

@router.get("/electricity/prices", response_model=List[ElectricityPriceInterval])
def read_electricity_prices(interval: str = Query("15min", pattern="^(15min|1h)$"),
                           session: Session = Depends(get_session)):
    """Get electricity data from database, queried by 15min or 1h interval."""
    return get_electricity_prices(session, interval)

@router.get("/electricity/average-10d", response_model=AvgElectricityPrice)
def get_10_day_avg(session: Session = Depends(get_session)):
    """Returns the average electricity price from the last 10 days up to the current moment."""
    avg = calculate_10_day_avg(session)
    return AvgElectricityPrice(
        start_window=datetime.now(tz=timezone.utc)-timedelta(days=10),
        end_window=datetime.now(),
        average_price=avg
    )
