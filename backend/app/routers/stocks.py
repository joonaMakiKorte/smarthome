from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, delete
from app.database import get_session
from app.services import stocks_service
from app.utils import handle_upstream_errors
from typing import List
from app.schemas import StockHistoryData
from app.models import Stock, StockQuote
import logging

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

@router.get("/stocks/watchlist", response_model=List[Stock])
def get_watchlist(session: Session = Depends(get_session)):
    """Get current stock watchlist from db"""
    symbols = session.exec(select(Stock)).all()
    return symbols

@router.post("/stocks/watchlist")
def add_stock(stock: Stock, session: Session = Depends(get_session)):
    """Add a new stock to watchlist"""
    try:
        session.add(stock)
        session.commit()
        session.refresh(stock)
        return stock
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Stock already in watchlist"
        )
    
@router.delete("/stocks/watchlist/{symbol}")
def remove_stock(symbol: str, session: Session = Depends(get_session)):
    """Delete a stock from watchlist"""
    stock = session.get(Stock, symbol)
    if not stock:
        logger.error("Error deleting stock from watchlist.")
        raise HTTPException(
            status_code=404,
            detail="Stock not found"
        )
    session.delete(stock)
    session.commit()
    return {"status" : "Stock deleted"}

@router.get("/stocks/quotes", response_model=List[StockQuote])
async def get_stock_quotes(
    symbols: str = Query(..., description="Comma separated symbols, e.g. 'AAPL' or 'AAPL,MSFT'"),
    session: Session = Depends(get_session)):
    """Get real-time stock quotes from Twelve Data"""
    async with handle_upstream_errors("Twelve Data"):
        return await stocks_service.get_smart_stock_quote(symbols, session)
    
@router.get("/stocks/history", response_model=List[StockHistoryData])
async def get_historical_data(
    symbols: str = Query(..., description="Comma separated symbols, e.g. 'AAPL' or 'AAPL,MSFT'"),
    interval: str = Query("5min", description="Timeframe: 1min, 5min, 1h"),
    session: Session = Depends(get_session)
):
    """Get historical data for stocks."""
    async with handle_upstream_errors("Twelve Data"):
        return await stocks_service.get_smart_stock_history(symbols, interval, session)
    
@router.delete("/stocks/history/prune")
def prune_stock_history(session: Session = Depends(get_session)):
    """Prune history older than 72 hours."""
    stocks_service.prune_db_history(session)
    return {"status" : "Stock history pruned."}
