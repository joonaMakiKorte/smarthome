import json
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

CONFIG_PATH = Path("config.json")

# Data models

class LocationConfig(BaseModel):
    """Represents the geolocation configuration."""
    lat: Optional[float] = None
    lon: Optional[float] = None
    city: Optional[str] = None
    country: Optional[str] = None

class AppConfig(BaseModel):
    """Main application configuration."""
    location: LocationConfig = Field(default_factory=LocationConfig)

# Configuration management functions

def load_config() -> AppConfig:
    if not CONFIG_PATH.exists():
        return AppConfig()
    
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
            return AppConfig(**data)
    except Exception:
        return AppConfig()
    
def save_config(config: AppConfig):
    with open(CONFIG_PATH, "w") as f:
        f.write(config.model_dump_json(indent=4, exclude_none=True))

# Update functions

def update_location(lat: float, lon: float, city: str, country: str):
    config = load_config()
    config.location.lat = lat
    config.location.lon = lon
    config.location.city = city
    config.location.country = country
    save_config(config)