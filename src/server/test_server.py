import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.server.main import app, get_session

# Banco de dados de teste em memória
sqlite_url = "sqlite://"
engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_register_and_login(client: TestClient):
    # Register
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 201

    # Login
    response = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token is not None

def test_history_sync(client: TestClient):
    # Register & Login
    client.post(
        "/auth/register",
        json={"username": "syncuser", "email": "sync@example.com", "password": "password123"}
    )
    login_res = client.post(
        "/auth/token",
        data={"username": "syncuser", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add history
    item = {
        "video_id": "xyz123",
        "title": "Test Video",
        "url": "https://youtube.com/watch?v=xyz123"
    }
    response = client.post("/history", json=item, headers=headers)
    assert response.status_code == 201

    # Get history
    response = client.get("/history", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Video"
