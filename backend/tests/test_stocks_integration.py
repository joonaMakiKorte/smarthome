import pytest
from datetime import datetime

# pytest tests/test_stocks_integration.py::test_real_stock_quotes
@pytest.mark.asyncio
async def test_real_stock_quotes(async_client, mocker):
    """Test fetching real stock quotes from api"""
    # Disable cache
    mocker.patch("app.services.stocks_service.memory_cache", {})

    # Request real data for Apple and Microsoft
    symbols = "AAPL,MSFT"
    response = await async_client.get(f"/stocks/quotes?symbols={symbols}")

    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) == 2 
    
    # We don't know the exact price, but it should be positive
    aapl_data = next(item for item in data if item["symbol"] == "AAPL")
    
    assert aapl_data["close"] > 0
    assert aapl_data["volume"] > 0
    assert isinstance(aapl_data["percent_change"], float)

# pytest tests/test_stocks_integration.py::test_real_stock_history
@pytest.mark.asyncio
async def test_real_stock_history(async_client, mocker):
    """Verify timezone and sparkline data conversion."""
    # Disable cache
    mocker.patch("app.services.stocks_service.memory_cache", {})

    symbol = "NVDA"
    interval = "1min"
    
    response = await async_client.get(f"/stocks/history?symbols={symbol}&interval={interval}")

    assert response.status_code == 200, f"API failed with: {response.text}"
    data = response.json()
    
    assert len(data) == 1
    stock_obj = data[0]
    
    assert stock_obj["symbol"] == "NVDA"

    latest_entry = stock_obj["history"][0] 
    
    assert isinstance(latest_entry["price"], float)
    assert latest_entry["price"] > 0
    
    # Ensure time is a valid ISO string
    time_str = latest_entry["timestamp"].replace("Z", "+00:00") # Satisfy python < 3.11
    dt = datetime.fromisoformat(time_str)
    assert dt.year >= 2023 # Sanity check 
