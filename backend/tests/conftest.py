import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import get_session

@pytest.fixture(name="session")
def session_fixture():
    """
    Creates a fresh in-memory SQLite database for every test function.
    """
    # Use StaticPool to share the same in-memory DB across requests
    engine = create_engine(
        "sqlite:///:memory:", 
        connect_args={"check_same_thread": False}, 
        poolclass=StaticPool 
    )
    
    SQLModel.metadata.create_all(engine)
    
    # Yield the session to the test
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Returns a TestClient that uses the mock database session.
    """
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    
    yield client

    # Cleanup
    app.dependency_overrides.clear()