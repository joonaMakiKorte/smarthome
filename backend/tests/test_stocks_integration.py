import pytest

# pytest tests/test_stocks_integration.py::test_real_stock_quotes
@pytest.mark.asyncio
async def test_real_stock_quotes(async_client):
    """Test fetching real stock quotes from api"""
    # Request real data for Apple and Microsoft
    symbols = "AAPL,MSFT"
    response = await async_client.get(f"/stocks/quotes?symbols={symbols}")

    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) == 2 
    
    # We don't know the exact price, but it should be positive
    aapl_data = next(item for item in data if item["symbol"] == "AAPL")
    
    assert aapl_data["name"] == "Apple Inc."
    assert aapl_data["close"] > 0
    assert aapl_data["volume"] > 0
    assert isinstance(aapl_data["percent_change"], float)

# pytest tests/test_stocks_integration.py::test_real_stock_history
@pytest.mark.asyncio
async def test_real_stock_history(async_client):
    """Verify timezone and sparkline data conversion."""
    symbol = "NVDA"
    count = 5
    interval = "1min"
    
    response = await async_client.get(f"/stocks/history?symbols={symbol}&interval={interval}&count={count}")

    assert response.status_code == 200, f"API failed with: {response.text}"
    data = response.json()
    
    assert len(data) == 1
    stock_obj = data[0]
    
    assert stock_obj["symbol"] == "NVDA"
    assert len(stock_obj["history"]) == count 

    latest_entry = stock_obj["history"][0] 
    
    assert isinstance(latest_entry["price"], float)
    assert latest_entry["price"] > 0
    
    # Ensure time is a valid ISO string
    time_str = latest_entry["time"].replace("Z", "+00:00") # Satisfy python < 3.11
    from datetime import datetime
    dt = datetime.fromisoformat(time_str)
    assert dt.year >= 2023 # Sanity check 
