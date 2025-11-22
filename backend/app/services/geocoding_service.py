from app.schemas import GeoLocation
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
ZIP_CODE = os.getenv("ZIP_CODE", "00100") # Default to Helsinki postal code
COUNTRY_CODE = os.getenv("COUNTRY_CODE", "FI") # Default to Finland if not set

url = f"http://api.openweathermap.org/geo/1.0/zip?zip={ZIP_CODE},{COUNTRY_CODE}&appid={API_KEY}"

async def get_geolocation():
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return GeoLocation(
            name=data["name"],
            lat=data["lat"],
            lon=data["lon"],
            country=data["country"]
        )
    except Exception as e:
        print(f"Error fetching geolocation: {e}")
        return None