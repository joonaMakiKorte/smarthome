from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.database import get_session
from app.services import stocks_service
from app.utils import handle_upstream_errors
from typing import List
from app.schemas import StockQuoteData, StockHistoryData
from app.models import StockSymbol

router = APIRouter()

@router.get("/stocks/watchlist", response_model=List[StockSymbol])
def get_watchlist(session: Session = Depends(get_session)):
    """Get current stock watchlist from db"""
    symbols = session.exec(select(StockSymbol)).all()
    return symbols

@router.post("/stocks/watchlist")
def add_stock(stock: StockSymbol, session: Session = Depends(get_session)):
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
    stock = session.get(StockSymbol, symbol)
    if not stock:
        print("Error deleting stock from watchlist")
        raise HTTPException(
            status_code=404,
            detail="Stock not found"
        )
    session.delete(stock)
    session.commit()
    return {"status" : "Stock deleted"}

@router.get("/stocks/quotes", response_model=List[StockQuoteData])
async def get_stock_quotes(symbols: str = Query(..., description="Comma separated symbols, e.g. 'AAPL' or 'AAPL,MSFT'")):
    """Get real-time stock quotes from Twelve Data"""
    async with handle_upstream_errors("Twelve Data"):
        return await stocks_service.get_realtime_market_data(symbols)
    
@router.get("/stocks/history", response_model=List[StockHistoryData])
async def get_historical_data(
    symbols: str = Query(..., description="Comma separated symbols, e.g. 'AAPL' or 'AAPL,MSFT'"),
    interval: str = Query("1day", description="Timeframe: 1min, 5min, 1h, 1day"),
    count: int = Query(30, description="Number of data points to return")
):
    """Get historical data for stocks."""
    async with handle_upstream_errors("Twelve Data"):
        return await stocks_service.get_stock_history(symbols,interval,count)
    