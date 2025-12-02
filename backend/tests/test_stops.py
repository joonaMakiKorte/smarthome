import pytest
from app.models import StopWatchlist
from sqlmodel import select
from unittest.mock import MagicMock, AsyncMock

# Raw GraphQL Response from Digitransit
RAW_GRAPHQL_DATA = {
    "data": {
        "stop": {
            "name": "Hakametsä",
            "stoptimesWithoutPatterns": [
                {
                    "realtime": True,
                    "realtimeArrival": 43200,    # 12:00:00 PM (Seconds since midnight)
                    "scheduledArrival": 43200,
                    "serviceDay": 1704067200,    # 2024-01-01 00:00:00 UTC
                    "headsign": "Sorin Aukio",
                    "trip": {
                        "route": {
                            "shortName": "3"
                        }
                    }
                }
            ]
        }
    }
}

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
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = RAW_GRAPHQL_DATA
    mock_response.raise_for_status.return_value = None

    mock_client_instance = MagicMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client_context = MagicMock()
    mock_client_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_context.__aexit__ = AsyncMock(return_value=None)

    mocker.patch(
        "app.services.stops_service.httpx.AsyncClient",
        return_value=mock_client_context
    )

    response = await async_client.get("/stops/live-board?gtfs_ids=tampere:0001")

    # 1704067200 (Jan 1) + 43200 (12 hours) = Jan 1 at 12:00 UTC
    expected_timestamp = "2024-01-01T12:00:00Z" 

    # Expected Parsed Data
    expected_data = [{
        "gtfs_id": "tampere:0001",
        "name": "Hakametsä",
        "timetable": [{
            "arrival_time": expected_timestamp,
            "headsign": "Sorin Aukio",
            "route": "3"
        }]
    }]

    assert response.status_code == 200
    assert response.json() == expected_data
