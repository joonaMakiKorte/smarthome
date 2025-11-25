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

# URL for one call API
url = f"https://api.openweathermap.org/data/3.0/onecall?lat={LAT}&lon={LON}&units=metric&appid={API_KEY}"

async def get_hourly_weather_data() -> List[HourlyWeather]:
    url_hourly = f"{url}&exclude=current,minutely,daily,alerts"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url_hourly)
            response.raise_for_status()
            data = response.json()

        # Parse the hourly weather data
        raw_data = data.get("hourly", [])[:24]  # Get only the next 24 hours
        hourly_weather = []
        for entry in raw_data:
            icon_code = entry.get("weather", [{}])[0].get("icon", "")
            hourly_weather.append(HourlyWeather(
                timestamp = int(datetime.fromtimestamp(entry.get("dt",0)).strftime('%H')), # Extract hour from UNIX timestamp
                temperature = float(entry.get("temp", 0.0)),
                icon_code = icon_code,
                icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png" # Construct icon URL
            ))
        return hourly_weather

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return []
    