from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db import SessionLocal, init_db, Ride

app = FastAPI()

# Request body model
class RideRequest(BaseModel):
    user_id: int
    pickup: str
    destination: str

@app.on_event("startup")
def startup_event():
    init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/book_ride")
def book_ride(request: RideRequest, db: Session = Depends(get_db)):
    ride = Ride(user_id=request.user_id, pickup=request.pickup, destination=request.destination)
    db.add(ride)
    db.commit()
    db.refresh(ride)
    return {"ride_id": ride.ride_id, "status": ride.status}
