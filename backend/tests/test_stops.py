import pytest
from app.models import StopWatchlist
from sqlmodel import select
from datetime import datetime
from app.services.stops_service import _fetch_single_stop_data

# pytest tests/test_stops.py::test_stop_watchlist
def test_stop_watchlist(sync_client, session):
    """Test stop watchlist operations"""
    # Add a new stop
    payload = {"gtfs_id": "tampere:0001", "custom_name": "koti", "original_name": "Hakametsä"}
    add_response = sync_client.post("/stops/watchlist", json=payload)

    assert add_response.status_code == 200
    assert add_response.json() == payload

    symbols_in_db = session.exec(select(StopWatchlist)).all()
    assert len(symbols_in_db) == 1
    added_item = symbols_in_db[0]
    assert added_item.gtfs_id == "tampere:0001"

    # Test getting the stops
    get_response = sync_client.get("/stops/watchlist")

    assert get_response.status_code == 200
    assert get_response.json()[0] == payload
    
    # Test deleting the stop
    delete_response = sync_client.delete("/stops/watchlist/tampere:0001")

    assert delete_response.status_code == 200
    assert delete_response.json() == {"status" : "Stop deleted"}
    
    deleted_stop = session.get(StopWatchlist, "tampere:0001")
    assert deleted_stop is None

# pytest tests/test_stops.py::test_stop_liveboard
@pytest.mark.asyncio
async def test_stop_liveboard(async_client, mocker):
    """Test fetching liveboard data for stops"""
    mock_data = [{
        "gtfs_id" : "tampere:0001",
        "name" : "Hakametsä",
        "timetable" : [{
            "arrival_time" : datetime.now().isoformat(),
            "headsign" : "Sorin Aukio",
            "route" : "3"
        }
        ]
    }]
    mock_get = mocker.patch("app.services.stops_service.fetch_stop_data")
    mock_get.return_value = mock_data

    response = await async_client.get("/stops/live-board?gtfs_ids=tampere:0001")

    assert response.status_code == 200
    assert response.json() == mock_data
    mock_get.assert_called_once()
