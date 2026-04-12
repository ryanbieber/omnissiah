"""Maintenance items routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database.database import get_db
from database.models import MaintenanceItem, MaintenanceType
from pydantic import BaseModel

router = APIRouter()


class MaintenanceItemCreate(BaseModel):
    name: str
    description: str | None = None
    type: MaintenanceType
    interval_days: int | None = None
    interval_miles: int | None = None
    car_id: int | None = None
    estimated_cost: float = 0.0
    notes: str | None = None


class MaintenanceItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    interval_days: int | None = None
    interval_miles: int | None = None
    estimated_cost: float | None = None
    notes: str | None = None


class MaintenanceItemResponse(BaseModel):
    id: int
    name: str
    description: str | None
    type: str
    interval_days: int | None
    interval_miles: int | None
    car_id: int | None
    estimated_cost: float
    notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[MaintenanceItemResponse])
async def list_maintenance_items(
    maintenance_type: MaintenanceType | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all maintenance items"""
    query = db.query(MaintenanceItem)
    if maintenance_type:
        query = query.filter(MaintenanceItem.type == maintenance_type)
    return query.offset(skip).limit(limit).all()


@router.get("/{item_id}", response_model=MaintenanceItemResponse)
async def get_maintenance_item(item_id: int, db: Session = Depends(get_db)):
    """Get a specific maintenance item"""
    item = db.query(MaintenanceItem).filter(MaintenanceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Maintenance item not found")
    return item


@router.post("/", response_model=MaintenanceItemResponse)
async def create_maintenance_item(
    item: MaintenanceItemCreate,
    db: Session = Depends(get_db),
):
    """Create a new maintenance item"""
    db_item = MaintenanceItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.put("/{item_id}", response_model=MaintenanceItemResponse)
async def update_maintenance_item(
    item_id: int,
    item: MaintenanceItemUpdate,
    db: Session = Depends(get_db),
):
    """Update a maintenance item"""
    db_item = db.query(MaintenanceItem).filter(MaintenanceItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Maintenance item not found")

    update_data = item.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    db_item.updated_at = datetime.utcnow()

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}")
async def delete_maintenance_item(item_id: int, db: Session = Depends(get_db)):
    """Delete a maintenance item"""
    db_item = db.query(MaintenanceItem).filter(MaintenanceItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Maintenance item not found")

    db.delete(db_item)
    db.commit()
    return {"message": "Maintenance item deleted"}
