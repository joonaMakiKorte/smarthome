import pytest
from app.models import StockSymbol
from app.schemas import StockQuoteData
from sqlmodel import select
from datetime import datetime

# pytest tests/test_stocks.py::test_stock_watchlist
def test_stock_watchlist(sync_client, session):
    """Test stock watchlist operations"""
    # Test adding a new stock
    payload = {"symbol": "AAPL", "name": "Apple Inc."}
    add_response = sync_client.post("/stocks/watchlist", json=payload)

    assert add_response.status_code == 200
    assert add_response.json() == payload

    symbols_in_db = session.exec(select(StockSymbol)).all()
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
    
    deleted_symbol = session.get(StockSymbol, "AAPL")
    assert deleted_symbol is None

# pytest tests/test_stocks.py::test_get_stock_quotes
@pytest.mark.asyncio
async def test_get_stock_quotes(async_client, mocker):
    """Test getting quote from a single stock"""
    mock_data = [{
        "symbol":"AAPL",
        "name":"Apple Inc",
        "close":148.0,
        "change":-0.23,
        "percent_change":-0.17,
        "high":149.0,
        "low":147.0,
        "volume":60000000
    }]
    mock_get = mocker.patch("app.services.stocks_service.get_realtime_market_data")
    mock_get.return_value = mock_data

    response = await async_client.get("/stocks/quotes?symbols=AAPL")

    assert response.status_code == 200
    assert response.json() == mock_data
    mock_get.assert_called_once()

# pytest tests/test_stocks.py::test_get_stock_history
@pytest.mark.asyncio
async def test_get_stock_history(async_client, mocker):
    """Test getting history data from a stock"""
    mock_data = [{
        "symbol":"AAPL",
        "history":[{
            "time": datetime.now().isoformat(),
            "price": 1.1
            }]
    }]
    mock_get = mocker.patch("app.services.stocks_service.get_stock_history")
    mock_get.return_value = mock_data

    response = await async_client.get("/stocks/history?symbols=a&interval=1min&count=1")

    assert response.status_code == 200
    assert response.json() == mock_data
    mock_get.assert_called_once()
    