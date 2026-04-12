"""Chainlit integration for natural language interactions"""
from chainlit import on_chat_start, on_message, cl
import json
from database.database import SessionLocal
from database.models import MaintenanceItem, MaintenanceTask, MaintenanceType
from datetime import datetime, timedelta


@on_chat_start
async def start():
    """Initialize chat session"""
    cl.user_session.set("db", SessionLocal())
    await cl.Message(
        content="👋 Welcome to Omnissiah Maintenance Assistant!\n\n"
                "I can help you:\n"
                "- Add new maintenance tasks\n"
                "- Check upcoming maintenance\n"
                "- Update task status\n"
                "- Manage budgets\n"
                "- Ask about your vehicles\n\n"
                "What would you like to do?"
    ).send()


@on_message
async def main(message: cl.Message):
    """Process user messages with AI agent"""
    db = cl.user_session.get("db")
    
    # Extract user message
    user_input = message.content.lower()
    
    response = ""
    
    # Simple pattern matching for MVP - will be replaced by deep agent later
    if "upcoming" in user_input or "due" in user_input:
        response = await get_upcoming_maintenance(db)
    elif "add" in user_input or "create" in user_input:
        response = "I can help you add a new maintenance task. Please provide:\n- Task name\n- Type (house/car/lawn)\n- Next due date"
    elif "status" in user_input or "check" in user_input:
        response = await get_maintenance_status(db)
    elif "budget" in user_input:
        response = "Budget management - what would you like to know about your budgets?"
    else:
        response = "I didn't quite understand that. Could you be more specific? Try:\n- 'Show upcoming maintenance'\n- 'Add a new task'\n- 'Check my cars'"
    
    await cl.Message(content=response).send()


async def get_upcoming_maintenance(db) -> str:
    """Get upcoming maintenance tasks"""
    tasks = db.query(MaintenanceTask).filter(
        MaintenanceTask.status == "pending"
    ).all()
    
    if not tasks:
        return "No pending maintenance tasks. Great job staying on top of things! 🎉"
    
    response = "📋 **Upcoming Maintenance Tasks:**\n\n"
    for task in tasks[:5]:  # Show first 5
        item = task.maintenance_item
        days_until = (task.next_due - datetime.utcnow()).days
        response += f"- **{item.name}** (Due in {days_until} days)\n"
    
    if len(tasks) > 5:
        response += f"\n... and {len(tasks) - 5} more tasks"
    
    return response


async def get_maintenance_status(db) -> str:
    """Get maintenance status summary"""
    pending = db.query(MaintenanceTask).filter(MaintenanceTask.status == "pending").count()
    in_progress = db.query(MaintenanceTask).filter(MaintenanceTask.status == "in-progress").count()
    completed = db.query(MaintenanceTask).filter(MaintenanceTask.status == "completed").count()
    
    return (
        f"📊 **Maintenance Status:**\n"
        f"- ✅ Completed: {completed}\n"
        f"- 🔄 In Progress: {in_progress}\n"
        f"- ⏳ Pending: {pending}"
    )
