from fastapi import APIRouter
from backend.app.services.electricity_service import fetch_and_store_electricity_prices

router = APIRouter()  

@router.post("/electricity/refresh")
async def refresh_electricity_prices():
    """Endpoint to refresh electricity prices from external API."""
    await fetch_and_store_electricity_prices()
    return {"status": "Electricity prices refreshed successfully."}