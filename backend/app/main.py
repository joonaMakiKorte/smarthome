
from fastapi import FastAPI
from app.routers import todos

app = FastAPI()

app.include_router(todos.router)

@app.get("/")
async def read_root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# uvicorn app.main:app --reload