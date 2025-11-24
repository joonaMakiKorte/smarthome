import os
import httpx
from typing import List
from dotenv import load_dotenv
from app.schemas import HourlyWeather
from datetime import datetime

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
LAT = os.getenv("LAT")
LON = os.getenv("LON")

# URL for 24-hour forecast data in metric units
url = f"https://pro.openweathermap.org/data/2.5/forecast/hourly?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&cnt=24"

async def get_weather_data() -> List[HourlyWeather]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        # Parse the hourly weather data
        hourly_weather = []
        for entry in data.get("list", []):
            timestamp = datetime.fromtimestamp(entry.get("dt",0)).strftime('%H')
            temperature = entry.get("main", {}).get("temp", 0.0)
            icon_code = entry.get("weather", [{}])[0].get("icon", "")
            icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png" # Construct icon URL
            hourly_weather.append(HourlyWeather(
                timestamp=int(timestamp),
                temperature=temperature,
                icon_code=icon_code,
                icon_url=icon_url
            ))
        return hourly_weather

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return []
    