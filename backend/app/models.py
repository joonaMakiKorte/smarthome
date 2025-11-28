from sqlmodel import SQLModel, Field
from datetime import datetime, timezone

class CompletedTask(SQLModel, table=True):
    """Database model for a completed todo task."""
    id: str = Field(primary_key=True, description="Unique ID from Todoist")
    content: str = Field(description="The task description/title")
    priority: int = Field(
        ge=1,
        le=4,
        description="Priority level: 4 (Very Urgent) to 1 (Natural)")
    completed_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="UTC Timestamp when the task was completed")
    
class ElectricityPrice(SQLModel, table=True):
    """Database model for electricity price data."""
    start_time: datetime = Field(primary_key=True, description="Start time of the price interval in UTC")
    end_time: datetime = Field(description="End time of the price interval in UTC")
    price: float = Field(description="Electricity price in CT/kWh")

class StockSymbol(SQLModel, table=True):
    """Database model for a stock in watchlist."""
    symbol: str = Field(primary_key=True, description="Symbol ticker of the instrument")
    name: str | None = Field(default=None, description="Name of the stock")
    