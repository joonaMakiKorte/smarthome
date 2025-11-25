from typing import List
from fastapi import APIRouter, HTTPException, Depends
from app.services import openweather_service
from app.schemas import HourlyWeather

router = APIRouter()

@router.get("/weather/hourly", response_model=List[HourlyWeather])
async def get_hourly_weather():
    """Fetch hourly weather data from OpenWeather."""
    weather_data = await openweather_service.get_hourly_weather_data()
    if not weather_data:
        raise HTTPException(status_code=500, detail="Could not fetch weather data")
    return weather_data
