import os
import httpx
from dotenv import load_dotenv
from app.services import geocoding_service
from app.config import load_config, update_location

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

async def get_coordinates():
    """Get coordinates from the config or use geocoding service to fetch them."""
    config = load_config()
    if config.location.lat is not None and config.location.lon is not None:
        return config.location.lat, config.location.lon

    # Use geocoding service to fetch coordinates
    print("Config missing geolocation data, fetching...")
    geo_data = await geocoding_service.get_geolocation()

    # Save to config for future use
    update_location(geo_data.lat, geo_data.lon, geo_data.name, geo_data.country) 

    return geo_data.lat, geo_data.lon