from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

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

class StockQuoteData(BaseModel):
    """Schema for delailed daily stock quote data."""
    symbol: str = Field(..., description="Symbol ticker of the instrument")
    name: str = Field(..., description="Name of the stock")
    close: float = Field(..., ge=0, description="The current price in USD")
    change: float = Field(..., description="Daily change in USD")
    percent_change: float = Field(...,description="Daily change in percentages")
    high: float = Field(...,ge=0, description="Daily high price in USD")
    low: float = Field(...,ge=0, description="Daily low price in USD")
    volume: int = Field(...,ge=0, description="Volume/action in stock") 

class StockPriceEntry(BaseModel):
    """Schema for individual data point in stock price history."""
    time: datetime = Field(..., description="Timestamp of the recorded price")
    price: float = Field(..., ge=0, description="Price in USD")

class StockHistoryData(BaseModel):
    """Schema for stock price history response."""
    symbol: str = Field(..., description="Symbol ticker of the instrument")
    history: List[StockPriceEntry] = Field(..., description="List of recorded price entries")

class StopTimeEntry(BaseModel):
    """Schema for individual data point in stop timetable."""
    arrival_time: datetime = Field(...,description="Arrival time of transportation method in UTC")
    headsign: str = Field(..., description="Headsign of the transportation line")
    route: str = Field(..., "Short name of the route")

class StopTimetable(BaseModel):
    """Schema for a stop timetable."""
    name: str = Field(..., description="Name of the stop")
    timetable: List[StopTimeEntry] = Field(..., description="Main timetable of the stop")