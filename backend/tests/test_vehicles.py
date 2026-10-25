
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.main import password_hash
from app.models import User

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
def create_admin_and_get_token(client):
    db_override = app.dependency_overrides[get_db]
    db = next(db_override())

    admin = User(
        username="adminuser",
        hashed_password=password_hash.hash("AdminPass123!"),
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.close()

    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "adminuser",
            "password": "AdminPass123!",
        },
    )

    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def test_list_vehicles_returns_empty_list_initially(client):
    client.post(
        "/api/auth/register",
        json={"username": "testuser", "password": "password123"},
    )

    login_response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/vehicles",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_create_vehicle(client):
    token = create_admin_and_get_token(client)

    vehicle = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": 25000,
        "quantity": 3,
    }

    response = client.post(
        "/api/vehicles",
        json=vehicle,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["make"] == "Toyota"
    assert response.json()["model"] == "Camry"
    
def test_created_vehicle_appears_in_inventory(client):
    token = create_admin_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    vehicle = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": 25000,
        "quantity": 3,
    }

    create_response = client.post(
        "/api/vehicles",
        json=vehicle,
        headers=headers,
    )
    assert create_response.status_code == 201

    response = client.get("/api/vehicles", headers=headers)

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

def test_list_vehicles_requires_authentication(client):
    response = client.get("/api/vehicles")

    assert response.status_code == 401


def test_list_vehicles_with_valid_token(client):
    client.post(
        "/api/auth/register",
        json={
            "username": "keerthi",
            "password": "StrongPass123!",
        },
    )

    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "keerthi",
            "password": "StrongPass123!",
        },
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/vehicles",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []
def test_create_vehicle_requires_authentication(client):
    vehicle = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": 25000,
        "quantity": 3,
    }

    response = client.post("/api/vehicles", json=vehicle)

    assert response.status_code == 401
    
def test_regular_user_cannot_create_vehicle(client):
    client.post(
        "/api/auth/register",
        json={"username": "regularuser", "password": "password123"},
    )

    login_response = client.post(
        "/api/auth/login",
        data={"username": "regularuser", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    vehicle = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": 25000,
        "quantity": 3,
    }

    response = client.post(
        "/api/vehicles",
        json=vehicle,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    
def test_admin_can_update_vehicle(client):
    token = create_admin_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    vehicle = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": 25000,
        "quantity": 3,
    }

    create_response = client.post(
        "/api/vehicles",
        json=vehicle,
        headers=headers,
    )
    assert create_response.status_code == 201

    vehicle_id = create_response.json()["id"]

    updated_vehicle = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": 27000,
        "quantity": 5,
    }

    response = client.put(
        f"/api/vehicles/{vehicle_id}",
        json=updated_vehicle,
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["price"] == 27000
    assert response.json()["quantity"] == 5
    
    
def test_regular_user_cannot_update_vehicle(client):
    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "regularuser",
            "password": "UserPass123!",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "regularuser",
            "password": "UserPass123!",
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(
        "/api/vehicles/1",
        json={
            "make": "Toyota",
            "model": "Camry",
            "category": "Sedan",
            "price": 27000,
            "quantity": 5,
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_admin_can_delete_vehicle(client):
    token = create_admin_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    vehicle = {
        "make": "Honda",
        "model": "City",
        "category": "Sedan",
        "price": 15000,
        "quantity": 2,
    }

    create_response = client.post(
        "/api/vehicles",
        json=vehicle,
        headers=headers,
    )
    assert create_response.status_code == 201

    vehicle_id = create_response.json()["id"]

    response = client.delete(
        f"/api/vehicles/{vehicle_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Vehicle deleted successfully"

    inventory_response = client.get(
        "/api/vehicles",
        headers=headers,
    )
    assert all(
        item["id"] != vehicle_id
        for item in inventory_response.json()
    )
    
    
def test_regular_user_cannot_delete_vehicle(client):
    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "deleteuser",
            "password": "UserPass123!",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "deleteuser",
            "password": "UserPass123!",
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete(
        "/api/vehicles/1",
        headers=headers,
    )

    assert response.status_code == 403



def test_search_vehicles_by_make(client):
    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "searchuser",
            "password": "UserPass123!",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "searchuser",
            "password": "UserPass123!",
        },
    )
    assert login_response.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        )
    }

    admin_token = create_admin_and_get_token(client)
    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    for vehicle in [
        {
            "make": "Toyota",
            "model": "Camry",
            "category": "Sedan",
            "price": 25000,
            "quantity": 3,
        },
        {
            "make": "Honda",
            "model": "City",
            "category": "Sedan",
            "price": 15000,
            "quantity": 2,
        },
    ]:
        create_response = client.post(
            "/api/vehicles",
            json=vehicle,
            headers=admin_headers,
        )
        assert create_response.status_code == 201

    response = client.get(
        "/api/vehicles?make=Toyota",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["make"] == "Toyota"


def test_search_vehicles_by_model(client):
    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "modelsearch",
            "password": "UserPass123!",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "modelsearch",
            "password": "UserPass123!",
        },
    )
    assert login_response.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        )
    }

    admin_token = create_admin_and_get_token(client)
    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    for vehicle in [
        {
            "make": "Toyota",
            "model": "Camry",
            "category": "Sedan",
            "price": 25000,
            "quantity": 3,
        },
        {
            "make": "Honda",
            "model": "City",
            "category": "Sedan",
            "price": 15000,
            "quantity": 2,
        },
    ]:
        client.post(
            "/api/vehicles",
            json=vehicle,
            headers=admin_headers,
        )

    response = client.get(
        "/api/vehicles?model=Camry",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["model"] == "Camry"


def test_user_can_purchase_vehicle_and_quantity_decreases(client):
    admin_token = create_admin_and_get_token(client)
    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    vehicle = {
        "make": "Toyota",
        "model": "Camry",
        "category": "Sedan",
        "price": 25000,
        "quantity": 3,
    }

    create_response = client.post(
        "/api/vehicles",
        json=vehicle,
        headers=admin_headers,
    )
    assert create_response.status_code == 201
    vehicle_id = create_response.json()["id"]

    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "buyeruser",
            "password": "BuyerPass123!",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "buyeruser",
            "password": "BuyerPass123!",
        },
    )
    assert login_response.status_code == 200

    user_headers = {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        )
    }

    response = client.post(
        f"/api/vehicles/{vehicle_id}/purchase",
        json={"quantity": 1},
        headers=user_headers,
    )

    assert response.status_code == 200

    inventory_response = client.get(
        "/api/vehicles",
        headers=user_headers,
    )
    purchased_vehicle = inventory_response.json()[0]

    assert purchased_vehicle["quantity"] == 2


def test_purchase_fails_when_stock_is_insufficient(client):
    admin_token = create_admin_and_get_token(client)
    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    create_response = client.post(
        "/api/vehicles",
        json={
            "make": "Honda",
            "model": "City",
            "category": "Sedan",
            "price": 15000,
            "quantity": 1,
        },
        headers=admin_headers,
    )
    assert create_response.status_code == 201
    vehicle_id = create_response.json()["id"]

    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "stockbuyer",
            "password": "BuyerPass123!",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "stockbuyer",
            "password": "BuyerPass123!",
        },
    )
    assert login_response.status_code == 200

    user_headers = {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        )
    }

    response = client.post(
        f"/api/vehicles/{vehicle_id}/purchase",
        json={"quantity": 2},
        headers=user_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient vehicle stock"

    inventory_response = client.get(
        "/api/vehicles",
        headers=user_headers,
    )
    assert inventory_response.json()[0]["quantity"] == 1


def test_admin_can_restock_vehicle(client):
    admin_token = create_admin_and_get_token(client)
    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    create_response = client.post(
        "/api/vehicles",
        json={
            "make": "Honda",
            "model": "City",
            "category": "Sedan",
            "price": 15000,
            "quantity": 2,
        },
        headers=admin_headers,
    )
    assert create_response.status_code == 201
    vehicle_id = create_response.json()["id"]

    response = client.post(
        f"/api/vehicles/{vehicle_id}/restock",
        json={"quantity": 5},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["quantity"] == 7


def test_regular_user_cannot_restock_vehicle(client):
    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "restockuser",
            "password": "UserPass123!",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "restockuser",
            "password": "UserPass123!",
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/vehicles/1/restock",
        json={"quantity": 5},
        headers=headers,
    )

    assert response.status_code == 403
