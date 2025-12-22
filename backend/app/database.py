import os
from sqlmodel import SQLModel, create_engine, Session

# Get DB_FILE form environment or default to "database.db" (local dev)
db_file = os.getenv("DB_FILE", "database.db")
sqlite_url = f"sqlite:///{db_file}"

# check_same_thread=False is needed for SQLite with FastAPI
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session