from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.database import get_session
from app.models import StopWatchlist
from app.schemas import StopTimetable
from app.services import stops_service
from app.utils import handle_upstream_errors
from typing import List

router = APIRouter()

@router.get("/stops/watchlist", response_model=List[StopWatchlist])
def get_stops(session: Session = Depends(get_session)):
    """Get all stops in watchlist"""
    stops = session.exec(select(StopWatchlist)).all()
    return stops

@router.post("/stops/watchlist", response_model=StopWatchlist)
def add_stop(stop: StopWatchlist, session: Session = Depends(get_session)):
    """Try adding a stop to watchlist"""
    try:
        session.add(stop)
        session.commit()
        session.refresh(stop)
        return stop
    except Exception:
        raise HTTPException(
            status_code=400,
              detail="Stop already in watchlist")
    
@router.delete("/stops/watchlist/{gtfs_id}")
def remove_stop(gtfs_id: str, session: Session = Depends(get_session)):
    """Delete a stop from watchlist"""
    stop = session.get(StopWatchlist, gtfs_id)
    if not stop:
        raise HTTPException(
            status_code=404,
            detail="Stop not found")
    session.delete(stop)
    session.commit()
    return {"status": "Stock deleted"}

@router.get("/stops/live-board", response_model=List[StopTimetable])
async def get_live_board(
    gtfs_ids: str = Query(..., description="Comma separated GTFS ids of stops, e.g. 'tampere:0001, tampere:0002'")
):
    """Get live timetables for requested stops"""
    async with handle_upstream_errors("Digitransit"):
        return await stops_service.fetch_stop_data(gtfs_ids)
    