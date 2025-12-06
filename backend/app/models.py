from sqlmodel import SQLModel, Field, Relationship, Column, BigInteger
from datetime import datetime, timezone
from typing import List, Optional

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


class Stock(SQLModel, table=True):
    """Database model for a stock in watchlist."""
    symbol: str = Field(primary_key=True, description="Symbol ticker of the instrument (e.g., AAPL)")
    name: str | None = Field(default=None, description="Name of the stock")

    quote: Optional["StockQuote"] = Relationship(
        back_populates="stock",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False}
    )
    history_entries: List["StockPriceEntry"] = Relationship(
        back_populates="stock", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"} # If stock is deleted, delete history
    )

class StockQuote(SQLModel, table=True):
    """Child table for detailed stock quote data."""
    symbol: str = Field(primary_key=True,foreign_key="stock.symbol",description="Symbol ticker of the instrument")
    name: str = Field(description="Name of the stock")
    close: float = Field(ge=0, description="The current price in USD")
    change: float = Field(description="Daily change in USD")
    percent_change: float = Field(description="Daily change in percentages")
    high: float = Field(ge=0, description="Daily high price in USD")
    low: float = Field(ge=0, description="Daily low price in USD")
    volume: int = Field(sa_column=Column(BigInteger),ge=0, description="Volume/action in stock") 
    timestamp: datetime = Field(description="Timestamp of the quote")
    
    stock: Stock = Relationship(back_populates="quote")

class StockPriceEntry(SQLModel, table=True):
    """Child table representing individual data points in stock timeseries data."""
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True, description="Timestamp of the recorded price")
    price: float = Field(..., ge=0, description="Price in USD")
    symbol: str = Field(foreign_key="stock.symbol", index=True)

    stock: Optional[Stock] = Relationship(back_populates="history_entries")


class StopWatchlist(SQLModel, table=True):
    """DB model for public transportation stop in watchlist."""
    gtfs_id: str = Field(primary_key=True, description="The GTFS ID (e.g., tampere:0001")
    custom_name: str = Field(description="A custom name for the stop")
    original_name: str | None = Field(default=None, description="Original stop name from API") 
       