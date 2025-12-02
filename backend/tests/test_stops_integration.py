import pytest
from datetime import datetime, timezone, timedelta

# pytest tests/test_stops_integration.py::test_fetch_real_liveboard
@pytest.mark.asyncio
async def test_fetch_real_liveboard(async_client):
    """Fetch real stop live-board data from API"""
    gtfs_id = "tampere:0821"
    response = await async_client.get(f"/stops/live-board?gtfs_ids={gtfs_id}")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    stop_data = data[0]
    assert "gtfs_id" in stop_data
    assert "name" in stop_data

    timetable = stop_data["timetable"]
    assert (len(timetable)) > 0

    # Assert next arrival is within 6h
    first_entry = timetable[0]
    arrival_time = datetime.fromisoformat(first_entry["arrival_time"].replace("Z", "+00:00"))
    now_utc = datetime.now(timezone.utc)
    lower_bound = now_utc - timedelta(minutes=1)
    upper_bound = now_utc + timedelta(hours=6)
    assert lower_bound <= arrival_time <= upper_bound
