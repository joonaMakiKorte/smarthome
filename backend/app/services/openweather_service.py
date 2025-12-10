import os
import httpx
import asyncio
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv
from app.schemas import HourlyWeather, CurrentWeather
from datetime import datetime, timezone, timedelta
from cachetools import TTLCache
from asyncache import cached

load_dotenv()

# API config
API_KEY = os.getenv("OPENWEATHER_API_KEY")
LAT = os.getenv("LAT")
LON = os.getenv("LON")
# URL for one call API
URL = f"https://api.openweathermap.org/data/3.0/onecall?lat={LAT}&lon={LON}&units=metric&appid={API_KEY}"

# Cache config
IS_TESTING = os.getenv("TESTING", "False") == "True"
CACHE_SIZE = 0 if IS_TESTING else 1
current_cache = TTLCache(maxsize=CACHE_SIZE, ttl=600)

@dataclass
class HourlyCache:
    """Hourly Weather State (Manual Cache)"""
    data: Optional[List[HourlyWeather]] = None
    expiry: Optional[datetime] = None
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock) # Prevent double-fetching

    @property
    def lock(self) -> asyncio.Lock:
        return self._lock

    def is_valid(self) -> bool:
        """Check if we have valid cached data"""
        now = datetime.now(timezone.utc)
        # Data is valid if it exists AND the current time is BEFORE the expiry time
        return bool(self.data and self.expiry and now < self.expiry)

    def update(self, new_data: List[HourlyWeather]):
        """Updates the cache and sets expiry to the top of the next hour"""
        now = datetime.now(timezone.utc)
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        self.data = new_data
        self.expiry = next_hour

# Init global cache instance
hourly_cache = HourlyCache()

async def fetch_hourly_weather_data() -> List[HourlyWeather]:
    # Check cache
    if hourly_cache.is_valid():
        return hourly_cache.data
    
    # Acquire lock to fetch new data
    async with hourly_cache.lock:
        # Double-check cache
        if hourly_cache.is_valid():
            return hourly_cache.data

        url_hourly = f"{URL}&exclude=current,minutely,daily,alerts"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url_hourly)
            response.raise_for_status()
            data = response.json()

        # Parse the hourly weather data
        raw_data = data.get("hourly", [])[:24]  # Get only the next 24 hours
        hourly_weather = []
        for entry in raw_data:
            icon_code = entry.get("weather", [{}])[0].get("icon", "")
            hourly_weather.append(HourlyWeather(
                timestamp = datetime.fromtimestamp(entry.get("dt",0), tz=timezone.utc), # Extract UNIX datetime
                temperature = float(entry.get("temp", 0.0)),
                icon_code = icon_code,
                icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png" # Construct icon URL
            ))

        # Update cache
        hourly_cache.update(hourly_weather)

        return hourly_weather
    
@cached(current_cache)
async def fetch_current_weather_data() -> CurrentWeather:
    url_current = f"{URL}&exclude=minutely,hourly,daily,alerts"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url_current)
        response.raise_for_status()
        data = response.json()

    current = data.get("current", {})
    icon_code = current.get("weather", [{}])[0].get("icon", "")
    return CurrentWeather(
        temperature = float(current.get("temp", 0.0)),
        temperature_feels_like= float(current.get("feels_like", 0.0)),
        humidity = int(current.get("humidity", 0)),
        wind_speed = float(current.get("wind_speed", 0.0)),
        description = current.get("weather", [{}])[0].get("description", ""),
        icon_code = icon_code,
        icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
    )
