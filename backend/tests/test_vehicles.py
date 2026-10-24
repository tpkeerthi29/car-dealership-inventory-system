
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_vehicles_returns_empty_list_initially():
    response = client.get("/api/vehicles")

    assert response.status_code == 200
    assert response.json() == []
