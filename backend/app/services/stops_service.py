import os
import httpx
from fastapi import HTTPException
from typing import List
from dotenv import load_dotenv
from app.schemas import StockQuoteData, StockPriceEntry, StockHistoryData
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()

API_KEY = os.getenv("DIGITRANSIT_API_KEY")
# Digitransit GraphQL endpoint
url = "https://api.digitransit.fi/routing/v2/waltti/gtfs/v1"

# GraphQL Query for stop timetable
STOP_QUERY
