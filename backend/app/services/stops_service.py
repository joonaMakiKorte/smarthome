import os
import httpx
import asyncio
from typing import List
from dotenv import load_dotenv
from app.schemas import StopTimeEntry, StopTimetable
from datetime import datetime, timezone

load_dotenv()

API_KEY = os.getenv("DIGITRANSIT_API_KEY")
# Digitransit GraphQL endpoint
URL = "https://api.digitransit.fi/routing/v2/waltti/gtfs/v1"

# GraphQL Query for stop timetable
STOP_QUERY = """
query getStopTimetable($stopId: String!) {
  stop(id: $stopId) {
    name
    stoptimesWithoutPatterns(numberOfDepartures: 10) {
      realtimeArrival
      scheduledArrival
      realtime
      serviceDay
      headsign
      trip {
        route {
          shortName
        }
      }
    }
  }
}
"""

async def fetch_stop_data(gtfs_ids: str) -> List[StopTimetable]:
    """Fetch data for all requested stops in parallel using a single connection pool"""
    # Extract stop ids from comma separated string
    stops = gtfs_ids.split(',')

    headers = {
        "Content-Type": "application/json",
        "digitransit-subscription-key": API_KEY
    }
    
    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        # Form a list of coroutine objects
        tasks = [_fetch_single_stop_data(client, stop) for stop in stops]
        # Run all tasks at once
        results = await asyncio.gather(*tasks)

    return results

async def _fetch_single_stop_data(client: httpx.AsyncClient, gtfs_id) -> StopTimetable:
    """Helper for fetching one stop using a shared client"""
    payload = {
        "query": STOP_QUERY,
        "variables": {"stopId": gtfs_id}
    }

    response = await client.post(URL, json=payload)
    response.raise_for_status()
    data = response.json()

    stop_data = data.get("data", {}).get("stop")
    arrivals = stop_data.get("stoptimesWithoutPatterns", [])
    return StopTimetable(
        id = gtfs_id, 
        name = stop_data.get("name"),
        timetable = [StopTimeEntry(
            arrival_time = _seconds_since_midnight_to_datetime(
                seconds_arrival=arrival.get("realtimeArrival") if arrival.get("realtime") is True
                  else arrival.get("scheduledArrival"),
                service_day=arrival.get("serviceDay")
            ),
            headsign = arrival.get("headsign"),
            route = arrival.get("trip", {}).get("route", {}).get("shortName")
        ) for arrival in arrivals]
    )

async def _seconds_since_midnight_to_datetime(seconds_arrival: int, service_day: int) -> datetime:
    """Convert seconds since midnight to utc datetime."""
    arrival_timestamp = service_day + seconds_arrival
    return datetime.fromtimestamp(arrival_timestamp, tz=timezone.utc)
