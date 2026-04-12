"""Budget management routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database.database import get_db
from database.models import Budget, BudgetExpense
from pydantic import BaseModel

router = APIRouter()


class BudgetCreate(BaseModel):
    name: str
    category: str
    limit: float
    month: int
    year: int
    notes: str | None = None


class BudgetUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    limit: float | None = None
    spent: float | None = None
    notes: str | None = None


class BudgetExpenseCreate(BaseModel):
    amount: float
    description: str


class BudgetExpenseResponse(BaseModel):
    id: int
    budget_id: int
    amount: float
    description: str
    date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class BudgetResponse(BaseModel):
    id: int
    name: str
    category: str
    limit: float
    spent: float
    month: int
    year: int
    notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[BudgetResponse])
async def list_budgets(
    category: str | None = None,
    month: int | None = None,
    year: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all budgets"""
    query = db.query(Budget)
    if category:
        query = query.filter(Budget.category == category)
    if month:
        query = query.filter(Budget.month == month)
    if year:
        query = query.filter(Budget.year == year)
    return query.offset(skip).limit(limit).all()


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(budget_id: int, db: Session = Depends(get_db)):
    """Get a specific budget"""
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.post("/", response_model=BudgetResponse)
async def create_budget(
    budget: BudgetCreate,
    db: Session = Depends(get_db),
):
    """Create a new budget"""
    db_budget = Budget(**budget.dict())
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    budget: BudgetUpdate,
    db: Session = Depends(get_db),
):
    """Update a budget"""
    db_budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    update_data = budget.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_budget, key, value)
    db_budget.updated_at = datetime.utcnow()

    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget


@router.delete("/{budget_id}")
async def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    """Delete a budget"""
    db_budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    db.delete(db_budget)
    db.commit()
    return {"message": "Budget deleted"}


@router.post("/{budget_id}/expenses", response_model=BudgetExpenseResponse)
async def add_budget_expense(
    budget_id: int,
    expense: BudgetExpenseCreate,
    db: Session = Depends(get_db),
):
    """Add an expense to a budget"""
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    db_expense = BudgetExpense(budget_id=budget_id, **expense.dict())
    budget.spent += expense.amount

    db.add(db_expense)
    db.add(budget)
    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.get("/{budget_id}/expenses", response_model=list[BudgetExpenseResponse])
async def get_budget_expenses(budget_id: int, db: Session = Depends(get_db)):
    """Get all expenses for a budget"""
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    return db.query(BudgetExpense).filter(BudgetExpense.budget_id == budget_id).all()
