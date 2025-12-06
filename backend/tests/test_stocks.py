import pytest
from app.models import Stock
from sqlmodel import select
from datetime import datetime
from zoneinfo import ZoneInfo

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
            "datetime": "2023-11-01 10:00:00",
            "open": "172.00",
            "high": "172.50",
            "low": "171.90",
            "close": "172.10",
            "volume": "1000"
        },
        {
            "datetime": "2023-11-01 09:59:00",
            "open": "171.00",
            "high": "171.50",
            "low": "170.90",
            "close": "171.20",
            "volume": "1500"
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

# pytest tests/test_stocks.py::test_get_stock_quotes
@pytest.mark.asyncio
async def test_get_stock_quotes(async_client, mock_httpx_client, mocker):
    """Test getting quote from a single stock"""
    mock_client = mock_httpx_client(
        patch_target="app.services.stocks_service.httpx.AsyncClient",
        response_data=RAW_QUOTE_DATA
    )
    mocker.patch("app.services.stocks_service.memory_cache", {})
    mocker.patch("app.services.stocks_service.token_manager.has_tokens", return_value=True)
    mocker.patch("app.services.stocks_service.rate_limiter.can_request", return_value=True)

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
        "timestamp": "2023-10-31T20:53:20-04:00"
    }]

    assert response.status_code == 200
    assert response.json() == expected_data
    mock_client.get.assert_called_once()

# pytest tests/test_stocks.py::test_get_stock_history
@pytest.mark.asyncio
async def test_get_stock_history(async_client, mock_httpx_client):
    """Test getting history data from a stock"""
    mock_client = mock_httpx_client(
        patch_target="app.services.stocks_service.httpx.AsyncClient",
        response_data=RAW_HISTORY_DATA
    )

    response = await async_client.get("/stocks/history?symbols=a&interval=1min&count=1")

    expected_data = [{
        "symbol": "AAPL",
        "history": [
            {
                # Oldest first (Reversed)
                "time": "2023-11-01T13:59:00Z", 
                "price": 171.20
            },
            {
                # Newest last
                "time": "2023-11-01T14:00:00Z",
                "price": 172.10
            }
        ]
    }]

    assert response.status_code == 200
    assert response.json() == expected_data
    mock_client.get.assert_called_once()
