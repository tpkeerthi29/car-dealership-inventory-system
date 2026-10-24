
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import User, Vehicle


password_hash = PasswordHash.recommended()
SECRET_KEY = "dev-only-change-this-before-deployment"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(username: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": username, "exp": expires_at}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Car Dealership Inventory API",
    lifespan=lifespan,
)


class VehicleCreate(BaseModel):
    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0)
    quantity: int = Field(ge=0)


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


@app.get("/api/vehicles")
def list_vehicles(db: Session = Depends(get_db)):
    return db.query(Vehicle).order_by(Vehicle.id).all()


@app.post("/api/vehicles", status_code=201)
def create_vehicle(
    vehicle_data: VehicleCreate,
    db: Session = Depends(get_db),
):
    vehicle = Vehicle(**vehicle_data.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@app.post("/api/auth/register", status_code=201)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter(User.username == user_data.username)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Username already exists",
        )

    user = User(
        username=user_data.username,
        hashed_password=password_hash.hash(user_data.password),
        role="user",
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Username already exists",
        )

    db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }
@app.post("/api/auth/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.username == form_data.username)
        .first()
    )

    if user is None or not password_hash.verify(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.username)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }