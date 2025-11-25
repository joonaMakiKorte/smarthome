from pydantic import BaseModel

class TodoTask(BaseModel):
    """Schema for an active todo task."""
    id: str
    content: str
    priority: int # (4=highest, 1=lowest)

class HourlyWeather(BaseModel):
    """Schema for hourly weather data."""
    timestamp: int # UNIX timestamp formatted to hour
    temperature: float
    icon_code: str # e.g., "10d"
    icon_url: str # Full URL to the weather icon

class CurrentWeather(BaseModel):
    """Schema for current weather data."""
    temperature: float
    temperature_feels_like: float  
    humidity: int
    wind_speed: float
    description: str
    icon_code: str
    icon_url: str