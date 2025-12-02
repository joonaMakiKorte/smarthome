import os
import httpx
from fastapi import HTTPException
from typing import List
from dotenv import load_dotenv
from app.schemas import StockQuoteData, StockPriceEntry, StockHistoryData
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()

API_KEY = os.getenv("TWELVEDATA_API_KEY")

async def fetch_realtime_market_data(symbols: str) -> List[StockQuoteData]:
    """Fetch real-time market data for selected symbols."""
    # Construct /quote endpoint url for symbols
    url = f"https://api.twelvedata.com/quote?symbol={symbols}&apikey={API_KEY}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

    if "code" in data and data["code"] != 200:
        raise HTTPException(
            status_code=400,
            detail=data.get("message")
        )

    results = []

    # For a single symbol, returns a dict with 'name' at root
    if "name" in data:
        results.append(StockQuoteData(
            symbol = data["symbol"],
            name = data["name"],
            close = round(float(data["close"]), 2),
            change = round(float(data["change"]), 2),
            percent_change = round(float(data["percent_change"]), 2),
            high = round(float(data["high"]), 2),
            low = round(float(data["low"]), 2),
            volume = int(data["volume"])
        ))
    # Twelve Data returns a dict keyed by symbol for multiple symbols requested
    else:
        for symbol, details in data.items():
            results.append(StockQuoteData(
                symbol = symbol,
                name = details["name"],
                close = round(float(details["close"]), 2),
                change = round(float(details["change"]), 2),
                percent_change = round(float(details["percent_change"]), 2),
                high = round(float(details["high"]), 2),
                low = round(float(details["low"]), 2),
                volume = int(details["volume"])
            ))
    return results

async def fetch_stock_history(symbols: str, interval: str, count: int) -> List[StockHistoryData]:
    """Fetch sparkline for given symbols"""
    # Construct /time_series endpoint url with given symbols and interval
    url = f"https://api.twelvedata.com/time_series?symbol={symbols}&interval={interval}&outputsize={count}&apikey={API_KEY}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

    if "code" in data and data["code"] != 200:
        raise HTTPException(
            status_code=400,
            detail=data.get("message")
        )
    
    results = []

    # For a single symbol, returns dict with 'values' at root
    if "values" in data:
        results.append(StockHistoryData(
            symbol = data["meta"]["symbol"],
            history = _process_values(data["values"], data["meta"]["exchange_timezone"])
        ))
    # For multiple symbols, returns dict keys for each symbol
    else: 
        for symbol, details in data.items():
            results.append(StockHistoryData(
                symbol = symbol,
                history = _process_values(details["values"], details["meta"]["exchange_timezone"])
        ))
    return results

def _process_values(values_list, tz_str) -> List[StockPriceEntry]:
    """
    Helper to extract stock price entries from time series endpoint.
    Uses timezone to conver datetime to UTC.
    """
    # Reverse data for correct order [Oldest -> Newest]
    reversed_data = values_list[::-1]

    return [StockPriceEntry(
        time = datetime.strptime(item["datetime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo(tz_str)).astimezone(ZoneInfo("UTC")),
        price = float(item["close"])
    ) for item in reversed_data]
