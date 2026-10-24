
from fastapi import FastAPI

app = FastAPI(title="Car Dealership Inventory API")


@app.get("/api/vehicles")
def list_vehicles():
    return []
