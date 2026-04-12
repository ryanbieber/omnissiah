"""Task execution skills for the deep maintenance agent

This module provides task execution capabilities. Skill knowledge is loaded
from skill.md files via skill_loader.py (see agents/skills/ folder).
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SkillType(str, Enum):
    """Types of executable skills (action-oriented, not knowledge)"""
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    LIST_TASKS = "list_tasks"
    SET_REMINDER = "set_reminder"
    UPDATE_VEHICLE = "update_vehicle"
    GET_STATUS = "get_status"
    CHECK_BUDGET = "check_budget"


class SkillExecutor:
    """Executes maintenance tasks via database operations"""
    
    def execute(self, skill_type: SkillType, parameters: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Execute a skill with given parameters.
        
        Args:
            skill_type: Type of skill to execute
            parameters: Parameters for the skill
            db: Database session
            
        Returns:
            Execution result with success status and data
        """
        try:
            if skill_type == SkillType.CREATE_TASK:
                return self._create_task(parameters, db)
            elif skill_type == SkillType.UPDATE_TASK:
                return self._update_task(parameters, db)
            elif skill_type == SkillType.LIST_TASKS:
                return self._list_tasks(parameters, db)
            elif skill_type == SkillType.SET_REMINDER:
                return self._set_reminder(parameters, db)
            elif skill_type == SkillType.UPDATE_VEHICLE:
                return self._update_vehicle(parameters, db)
            elif skill_type == SkillType.GET_STATUS:
                return self._get_status(parameters, db)
            elif skill_type == SkillType.CHECK_BUDGET:
                return self._check_budget(parameters, db)
            else:
                return {"success": False, "error": f"Unknown skill type: {skill_type}"}
        except Exception as e:
            logger.error(f"Skill execution error ({skill_type}): {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _create_task(self, params: Dict, db) -> Dict:
        """Create a maintenance task"""
        from database.models import MaintenanceItem, MaintenanceTask
        try:
            item = db.query(MaintenanceItem).filter_by(name=params.get("name")).first()
            if not item:
                item = MaintenanceItem(
                    name=params.get("name"),
                    description=params.get("description"),
                    type=params.get("type", "house")
                )
                db.add(item)
                db.flush()
            
            task = MaintenanceTask(
                maintenance_item_id=item.id,
                next_due=datetime.fromisoformat(params.get("due_date", datetime.now().isoformat())),
                status="pending"
            )
            db.add(task)
            db.commit()
            logger.info(f"Created task: {params.get('name')}")
            return {"success": True, "message": f"Created: {params.get('name')}", "task_id": task.id}
        except Exception as e:
            db.rollback()
            logger.error(f"Create task error: {e}")
            return {"success": False, "error": str(e)}
    
    def _update_task(self, params: Dict, db) -> Dict:
        """Update task status"""
        from database.models import MaintenanceTask
        try:
            task = db.query(MaintenanceTask).filter_by(id=params.get("task_id")).first()
            if not task:
                return {"success": False, "error": "Task not found"}
            
            task.status = params.get("status", "pending")
            if params.get("status") == "completed":
                task.last_completed = datetime.utcnow()
            
            db.commit()
            logger.info(f"Updated task {task.id} to {task.status}")
            return {"success": True, "message": f"Updated to {params.get('status')}"}
        except Exception as e:
            db.rollback()
            logger.error(f"Update task error: {e}")
            return {"success": False, "error": str(e)}
    
    def _list_tasks(self, params: Dict, db) -> Dict:
        """List tasks by status"""
        from database.models import MaintenanceTask
        try:
            query = db.query(MaintenanceTask)
            status = params.get("status")
            
            if status and status != "all":
                query = query.filter_by(status=status)
            
            tasks = query.limit(params.get("limit", 10)).all()
            task_list = []
            for task in tasks:
                task_list.append({
                    "id": task.id,
                    "name": task.maintenance_item.name if task.maintenance_item else "Unknown",
                    "status": task.status,
                    "due": task.next_due.strftime("%Y-%m-%d") if task.next_due else "N/A"
                })
            
            logger.info(f"Listed {len(task_list)} tasks")
            return {"success": True, "tasks": task_list, "count": len(task_list)}
        except Exception as e:
            logger.error(f"List tasks error: {e}")
            return {"success": False, "error": str(e)}
    
    def _set_reminder(self, params: Dict, db) -> Dict:
        """Set a reminder (creates a task with specific due date)"""
        try:
            days = params.get("days", 7)
            due_date = datetime.now() + timedelta(days=days)
            return self._create_task({
                "name": params.get("maintenance", "Maintenance Reminder"),
                "type": params.get("type", "car"),
                "due_date": due_date.isoformat(),
                "description": f"Reminder: {params.get('maintenance')}"
            }, db)
        except Exception as e:
            logger.error(f"Set reminder error: {e}")
            return {"success": False, "error": str(e)}
    
    def _update_vehicle(self, params: Dict, db) -> Dict:
        """Update vehicle mileage"""
        from database.models import Vehicle
        try:
            vehicle = db.query(Vehicle).filter_by(name=params.get("vehicle")).first()
            if not vehicle:
                return {"success": False, "error": "Vehicle not found"}
            
            vehicle.current_miles = params.get("miles", 0)
            db.commit()
            logger.info(f"Updated {vehicle.name} to {vehicle.current_miles} miles")
            return {"success": True, "message": f"Updated to {params.get('miles')} miles"}
        except Exception as e:
            db.rollback()
            logger.error(f"Update vehicle error: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_status(self, params: Dict, db) -> Dict:
        """Get maintenance status summary"""
        from database.models import MaintenanceTask
        try:
            pending = db.query(MaintenanceTask).filter_by(status="pending").count()
            in_progress = db.query(MaintenanceTask).filter_by(status="in-progress").count()
            completed = db.query(MaintenanceTask).filter_by(status="completed").count()
            
            logger.info(f"Status: {pending} pending, {in_progress} in progress, {completed} completed")
            return {
                "success": True,
                "pending": pending,
                "in_progress": in_progress,
                "completed": completed
            }
        except Exception as e:
            logger.error(f"Get status error: {e}")
            return {"success": False, "error": str(e)}
    
    def _check_budget(self, params: Dict, db) -> Dict:
        """Check budget status"""
        from database.models import Budget, BudgetExpense
        try:
            category = params.get("category", "maintenance")
            budget = db.query(Budget).filter_by(category=category).first()
            
            if not budget:
                return {"success": False, "error": "Budget not found"}
            
            spent = db.query(BudgetExpense).filter_by(budget_id=budget.id).count()
            percentage = (spent / budget.limit * 100) if budget.limit else 0
            
            logger.info(f"Budget {category}: ${spent}/${budget.limit} ({percentage:.1f}%)")
            return {
                "success": True,
                "category": category,
                "limit": budget.limit,
                "spent": spent,
                "percentage": percentage
            }
        except Exception as e:
            logger.error(f"Check budget error: {e}")
            return {"success": False, "error": str(e)}


# Single executor instance
skill_executor = SkillExecutor()


def create_maintenance_tools() -> List[dict]:
    """
    Create LLM tool definitions for LangChain DeepAgent SDK.
    
    Returns:
        List of tool definitions with descriptions and parameters
    """
    return [
        {
            "name": "create_task",
            "description": "Create a new maintenance task",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Task name"},
                    "type": {"type": "string", "enum": ["house", "car", "lawn"]},
                    "due_date": {"type": "string", "description": "YYYY-MM-DD format"},
                    "description": {"type": "string"}
                },
                "required": ["name", "type", "due_date"]
            }
        },
        {
            "name": "update_task",
            "description": "Update task status",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "status": {"type": "string", "enum": ["pending", "in-progress", "completed"]}
                },
                "required": ["task_id", "status"]
            }
        },
        {
            "name": "list_tasks",
            "description": "List maintenance tasks",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["pending", "in-progress", "completed", "all"]},
                    "limit": {"type": "integer", "default": 10}
                }
            }
        },
        {
            "name": "update_vehicle",
            "description": "Update vehicle mileage",
            "parameters": {
                "type": "object",
                "properties": {
                    "vehicle": {"type": "string"},
                    "miles": {"type": "integer"}
                },
                "required": ["vehicle", "miles"]
            }
        },
        {
            "name": "set_reminder",
            "description": "Set maintenance reminder",
            "parameters": {
                "type": "object",
                "properties": {
                    "maintenance": {"type": "string"},
                    "days": {"type": "integer", "default": 7},
                    "type": {"type": "string", "enum": ["house", "car", "lawn"]}
                },
                "required": ["maintenance"]
            }
        },
        {
            "name": "get_status",
            "description": "Get maintenance status summary",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "check_budget",
            "description": "Check budget status",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"}
                }
            }
        }
    ]
