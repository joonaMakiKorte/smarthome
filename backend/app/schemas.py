from pydantic import BaseModel, Field
from datetime import datetime

class TodoTask(BaseModel):
    """Schema for an active todo task."""
    id: str = Field(..., description="Unique ID from Todoist")
    content: str = Field(..., description="The task description/title")
    priority: int = Field(...,
                          ge=1,
                          le=4,
                          description="Priority level: 4 (Very Urgent) to 1 (Natural)")

class HourlyWeather(BaseModel):
    """Schema for hourly weather data."""
    timestamp: int = Field(..., ge=0, description="Hour of the day (0-23) or UNIX timestamp")
    temperature: float = Field(..., description="Temperature in Celsius")
    icon_code: str = Field(..., description="OWM icon code")
    icon_url: str = Field(..., description="Full URL to the weather icon image")

class CurrentWeather(BaseModel):
    """Schema for current weather data."""
    temperature: float = Field(..., description="Current temperature in Celsius")
    temperature_feels_like: float = Field(..., description="Human perception of temperature")
    humidity: int = Field(..., ge=0, le=100, description="Humidity percentage")
    wind_speed: float = Field(..., ge=0, description="Wind speed in m/s")
    description: str = Field(..., description="Text description (e.g. 'scattered clouds')")
    icon_code: str = Field(..., description="OWM icon code")
    icon_url: str = Field(..., description="Full URL to the weather icon image")
    