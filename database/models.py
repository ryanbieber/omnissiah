from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base
import enum


class MaintenanceType(str, enum.Enum):
    HOUSE = "house"
    CAR = "car"
    LAWN = "lawn"


class MaintenanceItem(Base):
    __tablename__ = "maintenance_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(Enum(MaintenanceType), nullable=False)
    interval_days = Column(Integer)  # Maintenance interval in days
    interval_miles = Column(Integer)  # For cars - interval in miles
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=True)
    estimated_cost = Column(Float, default=0.0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = relationship("MaintenanceTask", back_populates="maintenance_item")
    car = relationship("Car", back_populates="maintenance_items")


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"

    id = Column(Integer, primary_key=True, index=True)
    maintenance_item_id = Column(Integer, ForeignKey("maintenance_items.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, in-progress, completed
    last_completed = Column(DateTime)
    next_due = Column(DateTime, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    maintenance_item = relationship("MaintenanceItem", back_populates="tasks")
    history = relationship("TaskHistory", back_populates="task")


class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("maintenance_tasks.id"), nullable=False)
    status = Column(String(50), nullable=False)  # pending, in-progress, completed
    completed_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("MaintenanceTask", back_populates="history")


class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # e.g., "Ford Fiesta 2016 ST"
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    current_miles = Column(Integer, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    maintenance_items = relationship("MaintenanceItem", back_populates="car")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # maintenance, lawn, personal, etc.
    limit = Column(Float, nullable=False)
    spent = Column(Float, default=0.0)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BudgetExpense(Base):
    __tablename__ = "budget_expenses"

    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, index=True)
    agent_type = Column(String(100), nullable=False)  # chainlit, deep_agent, telegram_orchestrator
    input_data = Column(Text)  # JSON string of input
    output_data = Column(Text)  # JSON string of output
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
