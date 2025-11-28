import os
import httpx
from typing import List
from dotenv import load_dotenv
from app.schemas import StockQuoteData

load_dotenv()

API_KEY = os.getenv("TWELVEDATA_API_KEY")

# Symbols of stocks to fetch data from
symbols = ["SPX", "IXIC", "DJI", "OMXH25", "AAPL", "NVDA", "NOK", "META"]

async def get_realtime_market_data() -> List[StockQuoteData]:
    """
    Fetch real-time market data for selected symbols.
    """
    # Combine all symbols into one comma-separated string
    all_symbols = ",".join(symbols)
    url = f"https://api.twelvedata.com/quote?symbol={all_symbols}&apikey={API_KEY}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

    # Twelve Data returns a dict keyed by symbol for multiple symbols requested
    quote_data = []
    for symbol, details in data.items():
        quote_data.append(StockQuoteData(
            symbol = symbol,
            name = details["name"],
            close = round(float(details["close"]), 2),
            change = round(float(details["change"]), 2),
            percent_change = round(float(details["percent_change"]), 2),
            high = round(float(details["high"]), 2),
            low = round(float(details["low"]), 2),
            volume = int(details["volume"])
        ))
    return quote_data
