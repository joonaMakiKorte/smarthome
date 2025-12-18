import os
import httpx
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from typing import List
from dotenv import load_dotenv
from sqlmodel import Session, select, delete
from app.schemas import StockHistoryData
from app.models import Stock, StockQuote, StockPriceEntry
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from cachetools import TTLCache
from collections import deque

# API config
load_dotenv()
API_KEY = os.getenv("TWELVEDATA_API_KEY")  
DAILY_TOKENS = 800
TOKENS_PER_MIN = 8

# Market hours config
TZ_NY = ZoneInfo("America/New_York")
MARKET_OPEN = time(hour=9, minute=30)
MARKET_CLOSE = time(hour=16)

# Cache config
IS_TESTING = os.getenv("TESTING", "False") == "True"
CACHE_SIZE = 0 if IS_TESTING else 64
memory_cache = TTLCache(maxsize=CACHE_SIZE, ttl=60)


# --- Helper Managers ---

DAILY_CREDIT_LIMIT = 800  # Max 800 credits per day
RPM_LIMIT = 8             # Max 8 HTTP requests per min
TPM_LIMIT = 8             # Max 8 Tokens (symbols) per min
class APIGuard:
    """Separates RPM (Requests), TPM (Tokens/Minute), and Daily Quota."""
    def __init__(self):
        self._credits_used = 0
        self._request_timestamps = deque()
        self._token_timestamps = deque()   
        self._reset_daily_quota_if_needed()

    def _reset_daily_quota_if_needed(self):
        # Reset if the last check was a different day
        now_day = datetime.now(timezone.utc).date()
        if not hasattr(self, '_last_reset_date') or self._last_reset_date != now_day:
            self._credits_used = 0
            self._last_reset_date = now_day

    def can_proceed(self, symbol_count: int) -> bool:
        self._reset_daily_quota_if_needed()
        
        # Check Daily Limit
        if self._credits_used + symbol_count > DAILY_CREDIT_LIMIT:
            return False

        now = datetime.now().timestamp()

        # Check Request Limit (RPM)
        while self._request_timestamps and self._request_timestamps[0] < now - 60:
            self._request_timestamps.popleft()
        
        # We need to make 1 new request. If we are already at 8, we can't proceed.
        if len(self._request_timestamps) >= RPM_LIMIT:
            return False

        # Check Token Limit (TPM) - Clean and count
        while self._token_timestamps and self._token_timestamps[0] < now - 60:
            self._token_timestamps.popleft()

        # Check if we have enought tokens left for requested symbols
        if len(self._token_timestamps) + symbol_count > TPM_LIMIT:
            return False
            
        return True

    def record_usage(self, symbol_count: int):
        now = datetime.now().timestamp()
        self._credits_used += symbol_count
        self._request_timestamps.append(now)
        for _ in range(symbol_count):
            self._token_timestamps.append(now)

# Global singleton
api_guard = APIGuard()


# --- Market window helpers ---

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

def _get_target_session_window():
    """Returns the start and end datetime for the data we should display."""
    last_market_close = _get_last_market_close()
    target_date = datetime.now(TZ_NY).date() if last_market_close is None else last_market_close.date()
    start_dt = datetime.combine(target_date, MARKET_OPEN, TZ_NY)
    end_dt = datetime.combine(target_date, MARKET_CLOSE, TZ_NY)
    return start_dt, end_dt


# --- API functions ---
        
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

    # Normalize input
    items = [data] if "name" in data else data.values()

    # If market is closed, use market close timestamp for quote, else now
    close_timestamp = _get_last_market_close()
    quote_timestamp = datetime.now(timezone.utc) if close_timestamp is None else close_timestamp.astimezone(timezone.utc)
    for item in items:
        results.append(StockQuote(
            symbol=item["symbol"],
            name=item["name"],
            close=round(float(item["close"]), 2),
            change=round(float(item["change"]), 2),
            percent_change=round(float(item["percent_change"]), 2),
            high=round(float(item["high"]), 2),
            low=round(float(item["low"]), 2),
            volume=int(item["volume"]),
            timestamp=quote_timestamp
        ))
    return results

async def _fetch_stock_history(symbols: List[str], start_dt: datetime, end_dt: datetime, interval: str) -> List[StockHistoryData]:
    """Fetch sparkline for given symbols"""
    # Format dates to strings expected by Twelve Data
    start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    # Construct /time_series endpoint url with given symbols and interval
    symbols_str = ",".join(symbols)
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbols_str,
        "interval": interval,
        "start_date": start_str,
        "end_date": end_str,
        "apikey": API_KEY,
        "dp": 2,
        "order": 'ASC' 
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
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
            history = _process_values(data["values"], data["meta"]["exchange_timezone"], data["meta"]["symbol"], interval)
        ))
    # For multiple symbols, returns dict keys for each symbol
    else: 
        for symbol, details in data.items():
            results.append(StockHistoryData(
                symbol = symbol,
                history = _process_values(details["values"], details["meta"]["exchange_timezone"], symbol, interval)
        ))
    return results

def _process_values(values_list, tz_str, symbol: str, interval: str) -> List[StockPriceEntry]:
    """
    Helper to extract stock price entries from time series endpoint.
    Uses timezone to conver datetime to UTC.
    """
    return [StockPriceEntry(
        timestamp = datetime.strptime(item["datetime"], "%Y-%m-%d %H:%M:%S")
        .replace(tzinfo=ZoneInfo(tz_str))
        .astimezone(ZoneInfo("UTC")),
        price = float(item["close"]),
        interval = interval,
        symbol = symbol
    ) for item in values_list]


# --- DB helpers ---

def _bulk_save_quotes(session: Session, api_results: List[StockQuote]):
    """Save stock quotes to db and cache"""
    for quote in api_results:
        memory_cache[f"quote_{quote.symbol}"] = quote
        session.merge(quote)
    session.commit()

def _bulk_save_history(session: Session, api_results: List[StockHistoryData], interval: str, start_dt: datetime, end_dt: datetime):
    """Save stock history data to db and cache."""
    if not api_results:
        return

    # Convert window to UTC and make naive
    start_utc_naive = start_dt.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc_naive = end_dt.astimezone(timezone.utc).replace(tzinfo=None)
    
    symbols_to_update = [d.symbol for d in api_results]
    try:
        # Delete existing records for these symbols in this window
        statement = delete(StockPriceEntry).where(
            StockPriceEntry.symbol.in_(symbols_to_update),
            StockPriceEntry.interval == interval,
            StockPriceEntry.timestamp >= start_utc_naive,
            StockPriceEntry.timestamp <= end_utc_naive
        )
        session.exec(statement)

        # Add new records
        for stock_data in api_results:
            for entry in stock_data.history:
                # Create a NEW instance for the DB
                db_entry = StockPriceEntry(
                    symbol=stock_data.symbol,
                    interval=interval,
                    price=entry.price,
                    # Ensure NAIVE UTC
                    timestamp=entry.timestamp.astimezone(timezone.utc).replace(tzinfo=None)
                )
                session.add(db_entry)
            
            # Update Cache
            cache_key = f"history_{stock_data.symbol}{interval}"
            memory_cache[cache_key] = stock_data.history
        
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error saving history: {e}")
        raise e


# --- Public functions ---

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
        is_valid = False
        if db_data:
            ts_utc = db_data.timestamp.replace(tzinfo=timezone.utc) # Force UTC awareness

            # Check if DB data is fresh enough
            if last_market_close:
                db_ts_ny = ts_utc.astimezone(TZ_NY)
                
                if db_ts_ny.time() >= time(hour=15, minute=45): # 15 min buffer for market close
                    is_valid = True
            else:
                # Accept quotes newer than minute
                age = (datetime.now(timezone.utc) - ts_utc).total_seconds()
                if age < 60:
                    is_valid = True

        if is_valid:
            results[sym] = db_data
            memory_cache[f"quote_{sym}"] = db_data
        else:
            symbols_to_fetch.append(sym)

    if symbols_to_fetch:
        if api_guard.can_proceed(len(symbols_to_fetch)):
            api_data = await _fetch_realtime_market_data(symbols_to_fetch)
    
            # Record usage
            api_guard.record_usage(len(symbols_to_fetch))

            for quote in api_data:
                results[quote.symbol] = quote

            await run_in_threadpool(_bulk_save_quotes, session, api_data)
        else:
            # Fallback to existing DB data
            for sym in symbols_to_fetch:
                if sym in db_map:
                    results[sym] = db_map[sym]

    # Return quotes filtering out failures
    return [results[sym] for sym in symbol_list if sym in results]


async def get_smart_stock_history(symbols: str, interval: str, session: Session) -> List[StockHistoryData]:
    """Fetch stock sparlines ensuring token ratelimits and db fallback"""
    symbol_list = symbols.split(',')
    history_map = {sym: [] for sym in symbol_list}

    # Check for history in memory cache
    missing_symbols = []
    for sym in symbol_list:
        cache_key = f"history_{sym}{interval}"
        if cache_key in memory_cache:
            history_map[sym] = memory_cache[cache_key]
            continue
        missing_symbols.append(sym)

    if not missing_symbols:
        # All symbols were found in cache
        return [
            StockHistoryData(symbol=sym, history=history_map[sym]) 
            for sym in symbol_list
        ]

    # Fetch entries fitting the window from db
    start_dt, end_dt = _get_target_session_window()

    start_utc_naive = start_dt.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc_naive = end_dt.astimezone(timezone.utc).replace(tzinfo=None)
    db_entries_flat = await run_in_threadpool(lambda: session.exec(
        select(StockPriceEntry)
        .where(
            StockPriceEntry.symbol.in_(missing_symbols),
            StockPriceEntry.interval == interval,
            StockPriceEntry.timestamp >= start_utc_naive,
            StockPriceEntry.timestamp <= end_utc_naive
        )
        .order_by(StockPriceEntry.timestamp.asc())
    ).all())

    # Map entries to symbols
    for entry in db_entries_flat:
        if entry.symbol in history_map:
            history_map[entry.symbol].append(entry)

    # Determine which symbols are missing or stale
    now = datetime.now(TZ_NY)
    symbols_to_fetch = []
    
    is_active_session = start_dt.date() == now.date() and MARKET_OPEN <= now.time() < MARKET_CLOSE
    is_past_session = now > end_dt # Check if we are already over the session

    data_lifespan = 60 if interval == "1min" else 300 # Define expiration limit for data (1min or 5min)
    for sym in missing_symbols:
        entries = history_map[sym]
        if not entries:
            # No data in this window
            symbols_to_fetch.append(sym)
            continue

        last_ts_utc = entries[-1].timestamp.replace(tzinfo=timezone.utc)
        last_candle_time = last_ts_utc.astimezone(TZ_NY)

        # Session is active -> check if data is not expired
        if is_active_session:
            if (now - last_candle_time).total_seconds() > data_lifespan:
                symbols_to_fetch.append(sym)
            else:
                cache_key = f"history_{sym}{interval}"
                memory_cache[cache_key] = entries

        # Session has closed -> check if we have full data
        elif is_past_session:
            time_missing = (end_dt - last_candle_time).total_seconds()
            
            # Refetch if missing more than 10 minutes of data
            if time_missing > 600: 
                symbols_to_fetch.append(sym)
            else:
                cache_key = f"history_{sym}{interval}"
                memory_cache[cache_key] = entries
        
        # Pre-market
        else:
             cache_key = f"history_{sym}{interval}"
             memory_cache[cache_key] = entries

    if symbols_to_fetch:
        if api_guard.can_proceed(len(symbols_to_fetch)):
            api_results = await _fetch_stock_history(symbols_to_fetch, start_dt, end_dt, interval)

            # Record usage
            api_guard.record_usage(len(symbols_to_fetch))

            for stock_data in api_results:               
                history_map[stock_data.symbol] = stock_data.history

            await run_in_threadpool(_bulk_save_history, session, api_results, interval, start_dt, end_dt)

    # Get results
    return [StockHistoryData(symbol=sym, history=history_map[sym]) for sym in symbol_list]

def prune_db_history(session: Session):
    cutoff = datetime.now(TZ_NY) - timedelta(days=3)
    statement = delete(StockPriceEntry).where(StockPriceEntry.timestamp < cutoff)
    try:
        session.exec(statement)
        session.commit()
    except Exception as e:
        raise e