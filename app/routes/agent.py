"""Agent orchestration routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json
import logging
from database.database import get_db
from database.models import AgentExecution
from pydantic import BaseModel

logger = logging.getLogger(__name__)

try:
    from agents.deep_agent import DeepAgent
    deep_agent = DeepAgent()
except Exception as e:
    logger.warning(f"Failed to initialize DeepAgent: {e}")
    deep_agent = None

router = APIRouter()


class AgentExecutionRequest(BaseModel):
    agent_type: str  # chainlit, deep_agent, telegram_orchestrator
    input_data: dict


class AgentExecutionResponse(BaseModel):
    id: int
    agent_type: str
    input_data: str
    output_data: str | None
    status: str
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class CheckpointResponse(BaseModel):
    thread_id: str
    checkpoint_id: str | None
    data: dict
    timestamp: str | None


@router.post("/execute", response_model=AgentExecutionResponse)
async def execute_agent(
    request: AgentExecutionRequest,
    db: Session = Depends(get_db),
):
    """Execute an agent task"""
    db_execution = AgentExecution(
        agent_type=request.agent_type,
        input_data=json.dumps(request.input_data),
        status="pending",
    )
    db.add(db_execution)
    db.commit()
    db.refresh(db_execution)
    
    # TODO: Implement actual agent execution logic
    # This will be called by agents to register their tasks
    
    return db_execution


@router.get("/{execution_id}", response_model=AgentExecutionResponse)
async def get_agent_execution(execution_id: int, db: Session = Depends(get_db)):
    """Get agent execution status"""
    execution = db.query(AgentExecution).filter(AgentExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.get("/", response_model=list[AgentExecutionResponse])
async def list_agent_executions(
    agent_type: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all agent executions"""
    query = db.query(AgentExecution)
    if agent_type:
        query = query.filter(AgentExecution.agent_type == agent_type)
    if status:
        query = query.filter(AgentExecution.status == status)
    return query.order_by(AgentExecution.created_at.desc()).offset(skip).limit(limit).all()


@router.put("/{execution_id}", response_model=AgentExecutionResponse)
async def update_agent_execution(
    execution_id: int,
    request: AgentExecutionRequest,
    db: Session = Depends(get_db),
):
    """Update agent execution with results"""
    execution = db.query(AgentExecution).filter(AgentExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution.output_data = json.dumps(request.input_data)
    execution.status = "completed"
    execution.completed_at = datetime.utcnow()

    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


@router.get("/checkpoints/{user_id}", response_model=CheckpointResponse)
async def get_user_checkpoint(user_id: int):
    """
    Get latest checkpoint for a user.
    Uses LangChain's PostgresSaver to retrieve stored agent state.
    """
    thread_id = f"user_{user_id}"
    checkpoint = deep_agent.load_checkpoint(thread_id)
    
    if not checkpoint:
        return CheckpointResponse(
            thread_id=thread_id,
            checkpoint_id=None,
            data={},
            timestamp=None
        )
    
    return CheckpointResponse(
        thread_id=thread_id,
        checkpoint_id=checkpoint.get("id"),
        data=checkpoint.get("values", {}),
        timestamp=checkpoint.get("metadata", {}).get("timestamp")
    )


@router.get("/checkpoints/{user_id}/history", response_model=list[dict])
async def get_user_checkpoint_history(user_id: int):
    """
    Get all checkpoints for a user (conversation history).
    Uses LangChain's PostgresSaver to retrieve checkpoint history.
    """
    thread_id = f"user_{user_id}"
    history = deep_agent.get_all_checkpoints(thread_id)
    
    return [
        {
            "checkpoint_id": cp.get("id"),
            "timestamp": cp.get("metadata", {}).get("timestamp"),
            "data_keys": list(cp.get("values", {}).keys())
        }
        for cp in history
    ]


@router.post("/checkpoints/{user_id}/save")
async def save_checkpoint(user_id: int, data: dict):
    """
    Manually save a checkpoint for a user.
    """
    thread_id = f"user_{user_id}"
    checkpoint_id = deep_agent.save_checkpoint(thread_id, data)
    
    if not checkpoint_id:
        raise HTTPException(status_code=500, detail="Failed to save checkpoint")
    
    return {
        "thread_id": thread_id,
        "checkpoint_id": checkpoint_id,
        "timestamp": datetime.utcnow().isoformat()
    }
