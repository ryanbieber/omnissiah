"""Maintenance tasks routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database.database import get_db
from database.models import MaintenanceTask, TaskHistory
from pydantic import BaseModel

router = APIRouter()


class MaintenanceTaskCreate(BaseModel):
    maintenance_item_id: int
    next_due: datetime
    notes: str | None = None


class MaintenanceTaskUpdate(BaseModel):
    status: str | None = None
    last_completed: datetime | None = None
    next_due: datetime | None = None
    notes: str | None = None


class TaskHistoryResponse(BaseModel):
    id: int
    task_id: int
    status: str
    completed_at: datetime | None
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class MaintenanceTaskResponse(BaseModel):
    id: int
    maintenance_item_id: int
    status: str
    last_completed: datetime | None
    next_due: datetime
    notes: str | None
    created_at: datetime
    updated_at: datetime
    history: list[TaskHistoryResponse] = []

    class Config:
        from_attributes = True


@router.get("/", response_model=list[MaintenanceTaskResponse])
async def list_tasks(
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all maintenance tasks"""
    query = db.query(MaintenanceTask)
    if status:
        query = query.filter(MaintenanceTask.status == status)
    return query.offset(skip).limit(limit).all()


@router.get("/{task_id}", response_model=MaintenanceTaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task"""
    task = db.query(MaintenanceTask).filter(MaintenanceTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/", response_model=MaintenanceTaskResponse)
async def create_task(
    task: MaintenanceTaskCreate,
    db: Session = Depends(get_db),
):
    """Create a new maintenance task"""
    db_task = MaintenanceTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.put("/{task_id}", response_model=MaintenanceTaskResponse)
async def update_task(
    task_id: int,
    task: MaintenanceTaskUpdate,
    db: Session = Depends(get_db),
):
    """Update a maintenance task"""
    db_task = db.query(MaintenanceTask).filter(MaintenanceTask.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    db_task.updated_at = datetime.utcnow()

    # Create history entry
    history_entry = TaskHistory(
        task_id=task_id,
        status=update_data.get("status", db_task.status),
        completed_at=update_data.get("last_completed"),
    )
    db.add(history_entry)

    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a maintenance task"""
    db_task = db.query(MaintenanceTask).filter(MaintenanceTask.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted"}
