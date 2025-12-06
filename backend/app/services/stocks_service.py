import os
import httpx
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from typing import List
from dotenv import load_dotenv
from sqlmodel import Session, select
from app.schemas import StockHistoryData
from app.models import Stock, StockQuote, StockPriceEntry
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from cachetools import TTLCache
from collections import deque

# API config
load_dotenv()
API_KEY = os.getenv("TWELVEDATA_API_KEY")  
DAILY_TOKENS = 800
TOKENS_PER_MIN = 8

class RateLimiter:
    """Enforce 8 tokens/min constraint using a sliding window."""
    def __init__(self, max_requests: int = 8, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.timestamps = deque()

    def can_request(self) -> bool:
        now = datetime.now().timestamp()
        # Remove timestamps older than the window
        while self.timestamps and self.timestamps[0] < now - self.window_seconds:
            self.timestamps.popleft()
        return len(self.timestamps) < self.max_requests

    def record_request(self, count: int):
        for _ in range(count):
            self.timestamps.append(datetime.now().timestamp())

# Market hours config
TZ_NY = ZoneInfo("America/New_York")
MARKET_OPEN = time(hour=9, minute=30)
MARKET_CLOSE = time(hour=16)

class TokenManager:
    """Manages API token usage"""
    def __init__(self, reserve_per_h: int = 16):
        self._tokens = DAILY_TOKENS
        self._tokens_per_h = reserve_per_h # Tokens needed per hour when market is open

    def reset_tokens(self):
        self._tokens = DAILY_TOKENS

    def consume(self, amount: int = 1):
        self._tokens -= amount

    def has_tokens(self) -> bool:
        """Check if there are tokens left in budget after reserving for auto-updates"""
        reserved = 0
        now = datetime.now(TZ_NY)
        if self._is_market_open():
            reserved += (MARKET_CLOSE.hour - now.hour) * self._tokens_per_h
        elif now.weekday() <= 4 and now.time() <= MARKET_OPEN:
            # Market will open today
            reserved += (MARKET_CLOSE.hour - MARKET_OPEN.hour) * self._tokens_per_h
        
        return (self._tokens - reserved) > 0

    def _is_market_open(self) -> bool:
        """Check if US market is currently open (MON-FRI, 9:30-16:00 ET)"""
        now = datetime.now(TZ_NY)
        return now.weekday() <= 4 and (MARKET_OPEN <= now.time() <= MARKET_CLOSE)
    
# Init Global Managers
token_manager = TokenManager()
rate_limiter = RateLimiter()

# Cache config
memory_cache = TTLCache(maxsize=100, ttl=60)

def _get_last_market_close() -> datetime:
    """Calculate the timestamp of the most recent market close."""
    now = datetime.now(TZ_NY)
    today_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    if now.weekday() > 4:
        # Handle weekend case
        days_to_subtract = now.weekday() - 4
        return today_close - timedelta(days=days_to_subtract) 
    elif now.time() < MARKET_OPEN:
        # Handle Monday morning case
        days_back = 3 if now.weekday() == 0 else 1
        return today_close - timedelta(days=days_back)
    elif now.time() >= MARKET_CLOSE:
        # Handle market closed today
        return today_close
        
    return None # Market is currently OPEN
    
async def get_smart_stock_quote(symbols: str, session: Session) -> List[StockQuote]:
    """Get stock quotes ensuring token ratelimits and db fallback"""
    symbol_list = symbols.split(',')

    results = {}

    # Check in-memory cache
    missing_symbols = [] # Keep track of missing symbols
    for sym in symbol_list:
        cache_key = f"quote_{sym}"
        if cache_key in memory_cache:
            results[sym] = memory_cache[cache_key]
        else:
            missing_symbols.append(sym)

    # Everything was found in cache
    if not missing_symbols:
        return list(results.values())
    
    # Fetch quotes for missing symbols
    statement = select(StockQuote).where(StockQuote.symbol.in_(missing_symbols))
    db_quotes = await run_in_threadpool(lambda: session.exec(statement).all())
    db_map = {q.symbol: q for q in db_quotes} # Map symbols to quotes

    last_market_close = _get_last_market_close()

    # Validate db data against last market close
    symbols_to_fetch = [] # Keep track of missing symbols
    for sym in missing_symbols:
        db_data = db_map.get(sym)
        if db_data and last_market_close and db_data.timestamp >= last_market_close:
            results[sym] = db_data
            memory_cache[f"quote_{sym}"] = db_data
        else:
            symbols_to_fetch.append(sym)

    if symbols_to_fetch:
        # Check ratelimits
        if token_manager.has_tokens() and rate_limiter.can_request():
            api_data = await _fetch_realtime_market_data(symbols_to_fetch)

            rate_limiter.record_request()
            token_manager.consume(len(symbols_to_fetch))

            # Update to DB and Cache
            for quote in api_data:
                results[quote.symbol] = quote
                memory_cache[f"quote_{quote.symbol}"] = quote
                session.merge(quote)
            session.commit()
        else:
            # Fallback to existing DB data
            for sym in symbols_to_fetch:
                if sym in db_map:
                    results[sym] = db_map[sym]

    # Return quotes filtering out failures
    return [results[sym] for sym in symbols if sym in results]
        
async def _fetch_realtime_market_data(symbols: List[str]) -> List[StockQuote]:
    """Fetch real-time market data for selected symbols."""
    # Construct /quote endpoint url for symbols
    symbols_str = ",".join(symbols)
    url = f"https://api.twelvedata.com/quote?symbol={symbols_str}&apikey={API_KEY}"

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
        results.append(StockQuote(
            symbol = data["symbol"],
            name = data["name"],
            close = round(float(data["close"]), 2),
            change = round(float(data["change"]), 2),
            percent_change = round(float(data["percent_change"]), 2),
            high = round(float(data["high"]), 2),
            low = round(float(data["low"]), 2),
            volume = int(data["volume"]),
            timestamp=datetime.now(TZ_NY)
        ))
    # Twelve Data returns a dict keyed by symbol for multiple symbols requested
    else:
        for symbol, details in data.items():
            results.append(StockQuote(
                symbol = symbol,
                name = details["name"],
                close = round(float(details["close"]), 2),
                change = round(float(details["change"]), 2),
                percent_change = round(float(details["percent_change"]), 2),
                high = round(float(details["high"]), 2),
                low = round(float(details["low"]), 2),
                volume = int(details["volume"]),
                timestamp=datetime.now(TZ_NY)
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
        time = datetime.strptime(item["datetime"], "%Y-%m-%d %H:%M:%S")
        .replace(tzinfo=ZoneInfo(tz_str))
        .astimezone(ZoneInfo("UTC")),
        price = float(item["close"])
    ) for item in reversed_data]
