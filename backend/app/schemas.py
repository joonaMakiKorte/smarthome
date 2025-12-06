from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
from app.models import StockPriceEntry

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
    timestamp: datetime = Field(..., description="Timestamp in UTC")
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
    

class ElectricityPriceInterval(BaseModel):
    """Schema for electricity price response."""
    time: datetime = Field(..., description="Start time of the price interval in UTC")
    price: float = Field(..., ge=0, description="Electricity price of interval in CT/kWh")

class AvgElectricityPrice(BaseModel):
    """Schema for average electricity price in given time window."""
    start_window: datetime = Field(..., description="Start time of the average price window")
    end_window: datetime = Field(..., description="End time of the average price window")
    average_price: float = Field(..., ge=0, description="Average electricity price")


class StockHistoryData(BaseModel):
    """Schema for stock price history response."""
    symbol: str = Field(..., description="Symbol ticker of the instrument (e.g., AAPL)")
    history: List[StockPriceEntry] = Field(..., description="List of recorded price entries")


class StopTimeEntry(BaseModel):
    """Schema for individual data point in stop timetable."""
    arrival_time: datetime = Field(...,description="Arrival time of transportation method in UTC")
    headsign: str = Field(..., description="Headsign of the transportation line")
    route: str = Field(..., description="Short name of the route")

class StopTimetable(BaseModel):
    """Schema for a stop timetable."""
    gtfs_id: str = Field(..., description="GTFS id of the stop")
    name: str = Field(..., description="Name of the stop")
    timetable: List[StopTimeEntry] = Field(..., description="Main timetable of the stop")


class SensorData(BaseModel):
    """Schema for RuuviTag sensor data"""
    mac: str = Field(..., description="MAC address of the sensor")
    humidity: float = Field(..., ge=0, le=100, description="Recorded humidity percentage")
    temperature: float = Field(..., description="Recorded temperature in celcius")
    pressure: float = Field(..., ge=0, description="Recorder pressure in hPa")
    battery: int = Field(..., ge=0, description="Battery voltage in mV")
    rssi: int = Field(..., le=0, description="Received signal strength indicator")
    timestamp: datetime = Field(..., description="Timestamp of the recorded data")
    