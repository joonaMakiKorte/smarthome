from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from app.services import openweather_service
from app.schemas import HourlyWeather, CurrentWeather
from app.utils import handle_upstream_errors

router = APIRouter()

@router.get("/weather/hourly", response_model=List[HourlyWeather])
async def get_hourly_weather():
    """Fetch hourly weather data from OpenWeather."""
    async with handle_upstream_errors("OpenWeather"):
        return await openweather_service.get_hourly_weather_data()

@router.get("/weather/current", response_model=CurrentWeather)
async def get_current_weather():
    """Fetch current weather data from OpenWeather."""
    async with handle_upstream_errors("OpenWeather"):
        return await openweather_service.get_current_weather_data()