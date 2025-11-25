import os
import httpx
from typing import List
from dotenv import load_dotenv
from app.schemas import HourlyWeather, CurrentWeather
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
    
async def get_current_weather_data() -> CurrentWeather:
    url_current = f"{url}&exclude=minutely,hourly,daily,alerts"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url_current)
            response.raise_for_status()
            data = response.json()

        current = data.get("current", {})
        icon_code = current.get("weather", [{}])[0].get("icon", "")
        current_weather = CurrentWeather(
            temperature = float(current.get("temp", 0.0)),
            temperature_feels_like= float(current.get("feels_like", 0.0)),
            humidity = int(current.get("humidity", 0)),
            wind_speed = float(current.get("wind_speed", 0.0)),
            description = current.get("weather", [{}])[0].get("description", ""),
            icon_code = icon_code,
            icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
        )
        return current_weather
    
    except Exception as e:
        print(f"Error fetching current weather data: {e}")
        return None