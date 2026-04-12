"""Car management routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database.database import get_db
from database.models import Car
from pydantic import BaseModel

router = APIRouter()


class CarCreate(BaseModel):
    name: str
    make: str
    model: str
    year: int
    current_miles: int
    notes: str | None = None


class CarUpdate(BaseModel):
    name: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    current_miles: int | None = None
    notes: str | None = None


class CarResponse(BaseModel):
    id: int
    name: str
    make: str
    model: str
    year: int
    current_miles: int
    notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[CarResponse])
async def list_cars(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all cars"""
    return db.query(Car).offset(skip).limit(limit).all()


@router.get("/{car_id}", response_model=CarResponse)
async def get_car(car_id: int, db: Session = Depends(get_db)):
    """Get a specific car"""
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@router.post("/", response_model=CarResponse)
async def create_car(car: CarCreate, db: Session = Depends(get_db)):
    """Create a new car"""
    db_car = Car(**car.dict())
    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    return db_car


@router.put("/{car_id}", response_model=CarResponse)
async def update_car(
    car_id: int,
    car: CarUpdate,
    db: Session = Depends(get_db),
):
    """Update a car"""
    db_car = db.query(Car).filter(Car.id == car_id).first()
    if not db_car:
        raise HTTPException(status_code=404, detail="Car not found")

    update_data = car.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_car, key, value)
    db_car.updated_at = datetime.utcnow()

    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    return db_car


@router.delete("/{car_id}")
async def delete_car(car_id: int, db: Session = Depends(get_db)):
    """Delete a car"""
    db_car = db.query(Car).filter(Car.id == car_id).first()
    if not db_car:
        raise HTTPException(status_code=404, detail="Car not found")

    db.delete(db_car)
    db.commit()
    return {"message": "Car deleted"}
