import pytest
from sqlmodel import select
from app.models import ElectricityPrice
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, AsyncMock

RAW_PRICE_DATA = {
    "prices": [
        {
            "startDate": "2025-11-26T00:00:00Z",
            "endDate": "2024-11-26T01:00:00Z",
            "price": 50.0
        },
        {
            "startDate": "2025-11-26T01:00:00Z",
            "endDate": "2025-11-26T02:00:00Z",
            "price": 45.0
        }
    ]
}

RAW_EMPTY_PRICE_DATA = {
    "prices": []
}

# pytest tests/test_electricity.py::test_refreshing_electricity_prices
@pytest.mark.asyncio
async def test_refreshing_electricity_prices(async_client, mocker, session):
    """Test refreshing electricity prices from external API and storing them in DB."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = RAW_PRICE_DATA
    mock_response.raise_for_status.return_value = None

    mock_client_instance = MagicMock()
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client_context = MagicMock()
    mock_client_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_context.__aexit__ = AsyncMock(return_value=None)

    mocker.patch(
        "app.services.electricity_service.httpx.AsyncClient",
        return_value=mock_client_context
    )

    response = await async_client.post("/electricity/refresh")

    assert response.status_code == 200
    assert response.json() == {"status": "Electricity prices refreshed"}

    prices_in_db = session.exec(select(ElectricityPrice)).all()

    assert len(prices_in_db) == 2
    assert prices_in_db[0].price == 50.0
    assert prices_in_db[1].price == 45.0

# pytest tests/test_electricity.py::test_read_electricity_prices_15min
def test_read_electricity_prices_15min(sync_client, session):
    """Test fetching electricity prices with 15min interval"""
    time_now = datetime.now()
    price1 = ElectricityPrice(start_time=time_now, end_time=time_now+timedelta(minutes=15), price=5.00)
    price2 = ElectricityPrice(start_time=time_now+timedelta(minutes=15), end_time=time_now+timedelta(minutes=30), price=6.00)
    session.add(price1)
    session.add(price2)
    session.commit()

    response = sync_client.get("electricity/prices?interval=15min")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["price"] == price1.price

# pytest tests/test_electricity.py::test_read_electricity_prices_1h
def test_read_electricity_prices_1h(sync_client, session):
    """Test fetching electricity prices with 1h interval"""
    time_now = datetime.now().replace(minute=0, second=0, microsecond=0)
    price1 = ElectricityPrice(start_time=time_now, end_time=time_now+timedelta(minutes=15), price=5.00)
    price2 = ElectricityPrice(start_time=time_now+timedelta(minutes=15), end_time=time_now+timedelta(minutes=30), price=6.00)
    session.add(price1)
    session.add(price2)
    session.commit()

    response = sync_client.get("electricity/prices?interval=1h")

    assert response.status_code == 200

    # Prices should now collapse into one entry
    assert len(response.json()) == 1
    assert response.json()[0]["price"] == (price1.price + price2.price) / 2 # Should be average of the two prices

# pytest tests/test_electricity.py::test_calc_10_day_avg
def test_calc_10_day_avg(sync_client, session):
    """Test fetching 10 day avg price."""
    time_now = datetime.now(tz=timezone.utc)

    # Accepted data
    price1 = ElectricityPrice(start_time=time_now-timedelta(minutes=15), end_time=time_now, price=5.00)
    price2 = ElectricityPrice(start_time=time_now-timedelta(minutes=30), end_time=time_now-timedelta(minutes=15), price=10.0)
    
    # Excluded data
    price3 = ElectricityPrice(start_time=time_now-timedelta(days=11), end_time=time_now-timedelta(days=10), price=100.0)
    price4 = ElectricityPrice(start_time=time_now+timedelta(minutes=15), end_time=time_now+timedelta(minutes=30), price=50.0)

    session.add(price1)
    session.add(price2)
    session.add(price3)
    session.add(price4)

    session.commit()

    response = sync_client.get("electricity/average-10d")

    assert response.status_code == 200
    assert response.json()["average_price"] == (price1.price + price2.price) / 2

# pytest tests/test_electricity.py::test_delete_old_entry
@pytest.mark.asyncio
async def test_delete_old_entry(async_client, session, mocker):
    """Test auto deletion of entries older than 10 days"""
    time_now = datetime.now(tz=timezone.utc)

    # Accepted
    price1 = ElectricityPrice(start_time=time_now-timedelta(minutes=15), end_time=time_now, price=5.00)
    # Excluded
    price2 = ElectricityPrice(start_time=time_now-timedelta(days=11), end_time=time_now-timedelta(days=10), price=100.0)

    session.add(price1)
    session.add(price2)
    session.commit()

    # Patch empty data to only hit the deletion functionality
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = RAW_EMPTY_PRICE_DATA
    mock_response.raise_for_status.return_value = None

    mock_client_instance = MagicMock()
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client_context = MagicMock()
    mock_client_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_context.__aexit__ = AsyncMock(return_value=None)

    mocker.patch(
        "app.services.electricity_service.httpx.AsyncClient",
        return_value=mock_client_context
    )

    response = await async_client.post("/electricity/refresh")

    assert response.status_code == 200
    assert response.json() == {"status": "Electricity prices refreshed"}

    # Force the session to dump its cache and reload from the DB
    session.expire_all()

    # Only the first entry should be visible
    prices_in_db = session.exec(select(ElectricityPrice)).all()
    assert len(prices_in_db) == 1
    assert prices_in_db[0].price == price1.price