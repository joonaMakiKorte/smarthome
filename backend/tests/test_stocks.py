import pytest
from app.models import Stock
from sqlmodel import select
from app.models import StockPriceEntry
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

# Define the raw data for tests
RAW_QUOTE_DATA = {
    "symbol": "AAPL",
    "name": "Apple Inc",
    "exchange": "NASDAQ",
    "mic_code": "XNAS",
    "currency": "USD",
    "datetime": "2023-11-01",
    "timestamp": 1698800000,
    "open": "170.00",
    "high": "175.00",
    "low": "169.00",
    "close": "173.50",
    "volume": "50000000",
    "previous_close": "170.50",
    "change": "3.00",
    "percent_change": "1.75",
    "average_volume": "45000000",
    "is_market_open": False
}

RAW_HISTORY_DATA = {
    "meta": {
        "symbol": "AAPL",
        "interval": "1min",
        "currency": "USD",
        "exchange_timezone": "America/New_York",
        "exchange": "NASDAQ",
        "mic_code": "XNAS",
        "type": "Common Stock"
    },
    "values": [
        {
            "datetime": "2023-11-01 09:59:00",
            "open": "171.00",
            "high": "171.50",
            "low": "170.90",
            "close": "171.20",
            "volume": "1500"
        },
        {
            "datetime": "2023-11-01 10:00:00",
            "open": "172.00",
            "high": "172.50",
            "low": "171.90",
            "close": "172.10",
            "volume": "1000"
        }
    ]
}

TZ_NY = ZoneInfo("America/New_York")

# pytest tests/test_stocks.py::test_stock_watchlist
def test_stock_watchlist(sync_client, session):
    """Test stock watchlist operations"""
    # Test adding a new stock
    payload = {"symbol": "AAPL", "name": "Apple Inc."}
    add_response = sync_client.post("/stocks/watchlist", json=payload)

    assert add_response.status_code == 200
    assert add_response.json() == payload

    symbols_in_db = session.exec(select(Stock)).all()
    assert len(symbols_in_db) == 1
    added_item = symbols_in_db[0]
    assert added_item.symbol == "AAPL"

    # Test getting the stocks
    get_response = sync_client.get("/stocks/watchlist")

    assert get_response.status_code == 200
    assert get_response.json()[0] == payload
    
    # Test deleting the stock
    delete_response = sync_client.delete("/stocks/watchlist/AAPL")

    assert delete_response.status_code == 200
    assert delete_response.json() == {"status" : "Stock deleted"}
    
    deleted_symbol = session.get(Stock, "AAPL")
    assert deleted_symbol is None

# pytest tests/test_stocks.py::test_stock_pruning
def test_stock_pruning(sync_client, session):
    # Add two price entries
    time_now = datetime.now()
    price1 = StockPriceEntry(symbol="AAPL", interval="1min", timestamp=time_now-timedelta(days=4), price=0.0)
    price2 = StockPriceEntry(symbol="NVDA", interval="1min", timestamp=time_now, price=0.0)
    session.add(price1)
    session.add(price2)
    session.commit()

    response = sync_client.delete("/stocks/history/prune")
    assert response.status_code == 200

    db_entries = session.exec(select(StockPriceEntry)).all()
    assert len(db_entries) == 1
    assert db_entries[0].symbol == "NVDA"
    

# pytest tests/test_stocks.py::test_get_stock_quotes
@pytest.mark.asyncio
async def test_get_stock_quotes(async_client, mock_httpx_client, mocker):
    """Test getting quote from a single stock"""
    mock_client = mock_httpx_client(
        patch_target="app.services.stocks_service.httpx.AsyncClient",
        response_data=RAW_QUOTE_DATA
    )
    mocker.patch("app.services.stocks_service.memory_cache", {})

    response = await async_client.get("/stocks/quotes?symbols=AAPL")

    expected_data = [{
        "symbol": "AAPL",
        "name": "Apple Inc",
        "close": 173.50,
        "change": 3.00,
        "percent_change": 1.75,
        "high": 175.00,
        "low": 169.00,
        "volume": 50000000,
        "timestamp": "2023-11-01T00:53:20Z"
    }]

    assert response.status_code == 200
    assert response.json() == expected_data
    mock_client.get.assert_called_once()

# pytest tests/test_stocks.py::test_get_stock_history
@pytest.mark.asyncio
async def test_get_stock_history(async_client, mock_httpx_client, mocker):
    """Test getting history data from a stock"""
    mock_client = mock_httpx_client(
        patch_target="app.services.stocks_service.httpx.AsyncClient",
        response_data=RAW_HISTORY_DATA
    )
    mocker.patch("app.services.stocks_service.memory_cache", {})

    response = await async_client.get("/stocks/history?symbols=AAPL&interval=1min")

    expected_data = [{
        "symbol": "AAPL",
        "history": [
            {
                # Oldest first (Reversed)
                "symbol": "AAPL",
                "interval": "1min",
                "timestamp": "2023-11-01T13:59:00Z", 
                "price": 171.20
            },
            {
                # Newest last
                "symbol": "AAPL",
                "interval": "1min",
                "timestamp": "2023-11-01T14:00:00Z",
                "price": 172.10
            }
        ]
    }]

    assert response.status_code == 200
    assert response.json() == expected_data
    mock_client.get.assert_called_once()
