from fastapi import APIRouter, Depends, Query, HTTPException, status
from app.database import get_session
from sqlmodel import Session
from app.services import electricity_service
from app.utils import handle_upstream_errors
from typing import List
from app.schemas import ElectricityPriceInterval, AvgElectricityPrice
from datetime import datetime, timezone, timedelta

router = APIRouter()  

@router.post("/electricity/refresh")
async def refresh_electricity_prices(session: Session = Depends(get_session)):
    """Endpoint to refresh electricity prices from external API."""
    async with handle_upstream_errors("PORSSISAHKO.NET"):
        await electricity_service.fetch_and_store_electricity_prices(session)
        return {"status": "Electricity prices refreshed"}

@router.get("/electricity/prices", response_model=List[ElectricityPriceInterval])
def read_electricity_prices(interval: str = Query("15min", pattern="^(15min|1h)$"),
                           session: Session = Depends(get_session)):
    """Get electricity data from database, queried by 15min or 1h interval."""
    return electricity_service.get_electricity_prices(session, interval)

@router.get("/electricity/average-10d", response_model=AvgElectricityPrice)
def get_10_day_avg(session: Session = Depends(get_session)):
    """Returns the average electricity price from the last 10 days up to the current moment."""
    avg = electricity_service.calculate_10_day_avg(session)

    if avg is None:
        print("No electricity data found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No electricity data found for the last 10 days"
        )

    return AvgElectricityPrice(
        start_window=datetime.now(tz=timezone.utc)-timedelta(days=10),
        end_window=datetime.now(),
        average_price=avg
    )
