import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import get_session
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock

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

@pytest.fixture(name="sync_client")
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

@pytest_asyncio.fixture(name="async_client")
async def acync_client_fixture(session: Session):
    """
    Returns an httpx.AsyncClient that uses the mock database session.
    """
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    # Cleanup
    app.dependency_overrides.clear()
    
@pytest.fixture
def mock_httpx_client(mocker):
    """
    A factory fixture that patches httpx.AsyncClient with a mock context manager
    and mock response data.
    """
    def _mock_wrapper(patch_target, response_data, status_code=200):
        # Setup the Mock Response
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = response_data
        mock_response.raise_for_status.return_value = None

        # Setup the Client Instance (the object returned by __aenter__)
        mock_client_instance = MagicMock()
        # Mocking both get and post genericly covers most use cases
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.post = AsyncMock(return_value=mock_response)

        # Setup the Context Manager (the object initialized by AsyncClient())
        mock_client_context = MagicMock()
        mock_client_context.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_context.__aexit__ = AsyncMock(return_value=None)

        # Patch the target
        mocker.patch(patch_target, return_value=mock_client_context)

        return mock_client_instance

    return _mock_wrapper