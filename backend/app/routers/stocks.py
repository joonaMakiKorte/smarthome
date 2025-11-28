from fastapi import APIRouter
from app.services import stocks_service
from app.utils import handle_upstream_errors
from typing import List
from app.schemas import StockQuoteData

router = APIRouter()

@router.get("/stocks/quotes", response_model=List[StockQuoteData])
async def get_stock_quotes():
    """Get real-time stock quotes from Twelve Data"""
    async with handle_upstream_errors("Twelve Data"):
        return await stocks_service.get_realtime_market_data()