
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import todos, openweather, electricity, stocks, stops, ruuvitag
from contextlib import asynccontextmanager
from app.database import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Allow Vite frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(todos.router)
app.include_router(openweather.router)
app.include_router(electricity.router)
app.include_router(stocks.router)
app.include_router(stops.router)
app.include_router(ruuvitag.router)

@app.get("/")
async def read_root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# uvicorn app.main:app --reload