import pytest
from datetime import datetime, timezone, timedelta
from app.models import ElectricityPrice
from sqlmodel import select

# pytest tests/test_electricity_integration.py::test_refresh_real_electricity_prices
@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh_real_electricity_prices(async_client, session):
    """Test fetching real electricity price data."""
    # Add one old entry to db to check that deletion works
    time_now = datetime.now(tz=timezone.utc)
    price_entry= ElectricityPrice(start_time=time_now-timedelta(days=11), end_time=time_now-timedelta(days=10), price=100.0)
    old_key = price_entry.start_time # Save pk of the manually added entry before dump
    session.add(price_entry)
    session.commit()

    response = await async_client.post("/electricity/refresh")

    assert response.status_code == 200
    assert response.json() == {"status": "Electricity prices refreshed"}

    # Force the session to dump its cache and reload from the DB
    session.expire_all()

    # Old entry should be deleted
    assert session.get(ElectricityPrice, old_key) is None
    
    # There should be approx 192 entries in db now
    prices_in_db = session.exec(select(ElectricityPrice)).all()
    assert len(prices_in_db) > 190
    