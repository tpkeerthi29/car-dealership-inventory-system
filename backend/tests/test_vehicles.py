
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_list_vehicles_returns_empty_list_initially(client):
    response = client.get("/api/vehicles")

    assert response.status_code == 200
    assert response.json() == []


def test_create_vehicle(client):
    vehicle = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": 25000,
        "quantity": 3,
    }

    response = client.post("/api/vehicles", json=vehicle)

    assert response.status_code == 201
    data = response.json()
    assert data["make"] == "Toyota"
    assert data["model"] == "Camry"
    assert data["quantity"] == 3
    assert isinstance(data["id"], int)


def test_created_vehicle_appears_in_inventory(client):
    vehicle = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": 25000,
        "quantity": 3,
    }

    client.post("/api/vehicles", json=vehicle)
    response = client.get("/api/vehicles")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["make"] == "Toyota"

def test_register_user(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "keerthi",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "keerthi"
    assert "password" not in data


def test_register_duplicate_username_returns_conflict(client):
    user = {
        "username": "keerthi",
        "password": "StrongPass123!",
    }

    client.post("/api/auth/register", json=user)
    response = client.post("/api/auth/register", json=user)

    assert response.status_code == 409

def test_login_returns_access_token(client):
    client.post(
        "/api/auth/register",
        json={
            "username": "keerthi",
            "password": "StrongPass123!",
        },
    )

    response = client.post(
        "/api/auth/login",
        data={
            "username": "keerthi",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


def test_login_rejects_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={
            "username": "keerthi",
            "password": "StrongPass123!",
        },
    )

    response = client.post(
        "/api/auth/login",
        data={
            "username": "keerthi",
            "password": "WrongPass123!",
        },
    )

    assert response.status_code == 401


def test_login_rejects_unknown_username(client):
    response = client.post(
        "/api/auth/login",
        data={
            "username": "unknown_user",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 401
