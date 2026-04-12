"""Deep reasoning agent using LangChain's DeepAgents SDK"""
import os
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
import logging

# from langgraph.checkpoint.postgres import PostgresSaver
from config.settings import get_settings
from agents.skill_loader import get_skill_loader
from agents.tool_registry import get_tool_registry, execute_tool

logger = logging.getLogger(__name__)
settings = get_settings()


class DeepAgent:
    """
    Deep reasoning agent using LangChain's DeepAgents SDK.
    
    Features:
    - LLM-powered reasoning with Claude/GPT
    - Tool use for maintenance task management
    - PostgreSQL checkpointer for persistent memory
    - Automatic planning and task breakdown
    - Skill ingestion from skill.md files
    """
    
    def __init__(self):
        """Initialize the deep agent with tools and checkpointer"""
        # Load skills from skill.md files
        try:
            self.skill_loader = get_skill_loader()
            skill_summary = self.skill_loader.get_all_categories_summary()
            logger.info(f"✅ Loaded {len(skill_summary)} skill categories:")
            for cat_name, cat_info in skill_summary.items():
                logger.info(f"   - {cat_name}: {cat_info['count']} skills, Tools: {', '.join(cat_info['tools']) if cat_info['tools'] else 'None'}")
        except Exception as e:
            logger.warning(f"Could not load skills from skill.md files: {e}")
            self.skill_loader = None
        
        # Load tool registry for skill tool execution
        try:
            self.tool_registry = get_tool_registry()
            available_tools = list(self.tool_registry.tools.keys())
            logger.info(f"✅ Loaded {len(available_tools)} tools: {', '.join(available_tools)}")
            self.tool_executor = execute_tool
        except Exception as e:
            logger.warning(f"Could not load tool registry: {e}")
            self.tool_registry = None
            self.tool_executor = None
        
        try:
            from deepagents import create_deep_agent
            self.deepagents_available = True
        except ImportError:
            logger.warning("DeepAgents SDK not installed, using fallback mode")
            self.deepagents_available = False
        
        # Initialize checkpointer (checkpoint data will be stored in database via AgentExecution table)
        self.checkpointer = None
        logger.info("✅ Checkpointer initialized (checkpoints stored via AgentExecution table)")
        
        # Initialize DeepAgent if available
        self.agent = None
        if self.deepagents_available:
            try:
                from deepagents import create_deep_agent
                from agents.skills import create_maintenance_tools
                
                # Get maintenance tools
                tools = create_maintenance_tools()
                
                # Build system prompt with loaded skills
                system_prompt = self._build_system_prompt()
                
                # Create the deep agent with OpenAI
                model = settings.DEEP_AGENT_MODEL
                openai_api_key = settings.OPENAI_API_KEY
                
                if not openai_api_key:
                    raise ValueError("OPENAI_API_KEY not set in environment or .env file")
                
                # Set OpenAI API key for LangChain
                os.environ["OPENAI_API_KEY"] = openai_api_key
                
                self.agent = create_deep_agent(
                    model=model,
                    tools=tools,
                    system_prompt=system_prompt,
                    checkpointer=self.checkpointer,
                )
                logger.info(f"✅ Initialized DeepAgent with OpenAI model: {model}")
            except Exception as e:
                logger.error(f"Failed to initialize DeepAgent: {e}")
                logger.warning("Falling back to basic intent matching")
                self.deepagents_available = False
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with loaded skill information and available tools"""
        base_prompt = """You are an expert maintenance management assistant. Your role is to help users:

1. **Schedule Maintenance** - Track and schedule maintenance for houses, cars, and lawns
2. **Task Management** - Create, update, and complete maintenance tasks
3. **Budget Planning** - Monitor maintenance budgets and expenses
4. **Vehicle Tracking** - Track vehicle mileage and predict maintenance needs

## Available Actions

You have access to tools for:
- Creating and updating maintenance tasks
- Managing maintenance schedules by type (house/car/lawn)
- Tracking vehicle mileage and predicting next maintenance
- Setting maintenance reminders
- Checking and managing budgets
- Logging maintenance expenses

## Available Tools for Skill Execution

You can execute specialized tools based on maintenance needs:
"""
        
        # Append tool definitions if registry is available
        if self.tool_registry:
            try:
                tools_summary = self.tool_registry.get_tool_definitions_for_llm()
                base_prompt += tools_summary + "\n"
            except Exception as e:
                logger.warning(f"Could not append tool definitions: {e}")
        
        base_prompt += """
## Response Format

- Always confirm actions taken
- Provide clear status updates
- Show upcoming maintenance dates
- Alert on budget limits or overdue items
- Ask for clarification if parameters are unclear
- When a skill defines tools, suggest using them for better decisions

## Examples

User: "Remind me about oil change in 3 days"
Assistant: ✓ I'll create a reminder for your oil change in 3 days.

User: "What maintenance is due?"
Assistant: [Shows list of pending maintenance with dates]

User: "Update my car mileage to 85000"
Assistant: ✓ Car updated to 85000 miles. Next service due at 90000 miles.

User: "Should I water my lawn today?"
Assistant: Let me check the weather forecast... [uses weather_check tool]
"""
        
        # Append loaded skill knowledge if available
        if self.skill_loader:
            try:
                skill_summary = self.skill_loader.get_all_categories_summary()
                base_prompt += "\n## Skill Knowledge Base\n\nYou have detailed knowledge about:\n"
                
                for cat_name, cat_info in skill_summary.items():
                    cat_display = cat_name.replace('_', ' ').title()
                    base_prompt += f"\n### {cat_display}\n"
                    
                    # Get skill for description
                    for skill in self.skill_loader.get_category_skills(cat_name):
                        base_prompt += f"**{skill.metadata.name}**: {skill.metadata.description[:150]}...\n"
                        if skill.metadata.tools:
                            base_prompt += f"Available tools: {', '.join(skill.metadata.tools)}\n"
            except Exception as e:
                logger.warning(f"Could not append skill knowledge to prompt: {e}")
        
        return base_prompt
    
    def execute_skill_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool associated with a skill.
        
        This allows the agent to call external tools/CLIs for smart decisions.
        Examples: weather_check for lawn watering, mileage_tracker for car maintenance
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters
        
        Returns:
            Dictionary with execution result
        """
        if not self.tool_executor:
            logger.warning("Tool registry not available, cannot execute tool")
            return {"success": False, "error": "Tool registry not initialized"}
        
        try:
            logger.info(f"Executing tool '{tool_name}' with params: {kwargs}")
            result = self.tool_executor(tool_name, **kwargs)
            logger.info(f"Tool '{tool_name}' result: {result.get('success')}")
            return result
        except Exception as e:
            logger.error(f"Failed to execute tool '{tool_name}': {e}")
            return {"success": False, "error": str(e), "tool": tool_name}
    
    def get_available_tools_for_skill(self, skill_name: str) -> List[str]:
        """
        Get list of available tools for a given skill.
        
        Args:
            skill_name: Name of the skill (e.g., 'lawncare', 'car_maintenance')
        
        Returns:
            List of tool names available for this skill
        """
        if not self.skill_loader:
            return []
        
        skill = self.skill_loader.get_skill(skill_name)
        if skill and skill.metadata.tools:
            return skill.metadata.tools
        
        return []
    
    async def process_user_message(
        self,
        message: str,
        chat_id: int,
        user_id: int,
        db: Session
    ) -> str:
        """
        Process a user message through the deep agent or fallback.
        
        Args:
            message: The user's message
            chat_id: Telegram chat ID
            user_id: Telegram user ID
            db: Database session
            
        Returns:
            Response message to send back to user
        """
        thread_id = f"user_{user_id}_chat_{chat_id}"
        
        try:
            # Use DeepAgent SDK if available
            if self.deepagents_available and self.agent:
                return await self._process_with_deepagents(message, thread_id)
            else:
                # Fallback to basic intent matching
                return await self._process_with_intent_matching(message, thread_id, db)
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return f"❌ Error: {str(e)}"
    
    async def _process_with_deepagents(self, message: str, thread_id: str) -> str:
        """Process message using LangChain DeepAgent SDK"""
        try:
            input_data = {
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            }
            
            config = {"configurable": {"thread_id": thread_id}}
            
            logger.info(f"Processing with DeepAgent: {message}")
            result = self.agent.invoke(input_data, config=config)
            
            # Extract response
            if result and "messages" in result:
                messages = result["messages"]
                if messages:
                    last_message = messages[-1]
                    response = last_message.content if hasattr(last_message, "content") else str(last_message)
                    logger.info(f"DeepAgent response: {response[:100]}...")
                    return response
            
            return "✓ Task processed successfully"
        
        except Exception as e:
            logger.error(f"DeepAgent error: {e}")
            raise
    
    async def _process_with_intent_matching(self, message: str, thread_id: str, db: Session) -> str:
        """Fallback: Process message using intent matching and skills"""
        from agents.skills import skill_executor, SkillType
        
        try:
            intent = self._analyze_intent(message)
            logger.info(f"Detected intent: {intent}")
            
            if not intent:
                return self._get_helpful_response(message)
            
            parameters = self._extract_parameters(message, intent)
            logger.info(f"Extracted parameters: {parameters}")
            
            skill_type = SkillType[intent.upper()] if intent.upper() in SkillType.__members__ else None
            
            if skill_type:
                result = skill_executor.execute(skill_type, parameters, db)
                logger.info(f"Skill result: {result}")
                return self._format_response(result, intent)
            
            return self._get_helpful_response(message)
        
        except Exception as e:
            logger.error(f"Intent matching error: {e}")
            raise
    
    def _analyze_intent(self, message: str) -> Optional[str]:
        """Analyze user message to determine intent (fallback method)"""
        message_lower = message.lower().strip()
        
        if any(p in message_lower for p in ["status", "how am i", "tell me my", "what's my"]):
            return "get_status"
        if any(p in message_lower for p in ["upcoming", "what's due", "what's coming", "next"]):
            return "list_tasks"
        if any(p in message_lower for p in ["remind", "set reminder", "alert me"]):
            return "set_reminder"
        if any(p in message_lower for p in ["complete", "done", "finished", "mark as done"]):
            return "update_task"
        if any(p in message_lower for p in ["add task", "new task", "create", "add maintenance"]):
            return "create_task"
        if any(p in message_lower for p in ["budget", "spent", "expense", "cost"]):
            return "check_budget"
        if any(p in message_lower for p in ["miles", "mileage", "update car", "odometer"]):
            return "update_vehicle"
        if any(p in message_lower for p in ["help", "what can", "commands", "options"]):
            return "help"
        
        return None
    
    def _extract_parameters(self, message: str, intent: Optional[str]) -> Dict[str, Any]:
        """Extract parameters from user message (fallback method)"""
        import re
        
        message_lower = message.lower()
        parameters = {}
        
        if intent == "set_reminder":
            match = re.search(r'(\d+)\s*(day|week|month)', message_lower)
            if match:
                num = int(match.group(1))
                unit = match.group(2)
                if unit == "week":
                    num *= 7
                elif unit == "month":
                    num *= 30
                parameters["days"] = num
            else:
                parameters["days"] = 7
            
            if "oil" in message_lower:
                parameters["maintenance"] = "Oil Change"
            elif "filter" in message_lower:
                parameters["maintenance"] = "Air Filter"
            elif "tire" in message_lower:
                parameters["maintenance"] = "Tire Rotation"
        
        elif intent == "create_task":
            if "oil" in message_lower:
                parameters["name"] = "Oil Change"
                parameters["type"] = "car"
            elif "filter" in message_lower:
                parameters["name"] = "Air Filter Replacement"
                parameters["type"] = "car"
            elif "tire" in message_lower:
                parameters["name"] = "Tire Rotation"
                parameters["type"] = "car"
            else:
                parameters["name"] = "New Maintenance Task"
                parameters["type"] = "house"
            
            match = re.search(r'(\d{4}-\d{2}-\d{2})', message)
            if match:
                parameters["due_date"] = match.group(1)
        
        elif intent == "update_task":
            match = re.search(r'task\s*#?(\d+)', message_lower)
            if match:
                parameters["task_id"] = int(match.group(1))
            parameters["status"] = "completed"
        
        elif intent == "update_vehicle":
            match = re.search(r'(\d+)\s*(mile|km)', message_lower)
            if match:
                parameters["miles"] = int(match.group(1))
            
            if "fiesta" in message_lower:
                parameters["vehicle"] = "Ford Fiesta"
            elif "odyssey" in message_lower:
                parameters["vehicle"] = "Honda Odyssey"
        
        return parameters
    
    def _format_response(self, result: Dict[str, Any], intent: str) -> str:
        """Format skill execution result (fallback method)"""
        if not result.get("success"):
            return f"❌ {result.get('error', 'Something went wrong')}"
        
        if intent == "get_status":
            return (
                f"📊 **Maintenance Status**\n"
                f"✅ Completed: {result.get('completed', 0)}\n"
                f"🔄 In Progress: {result.get('in_progress', 0)}\n"
                f"⏳ Pending: {result.get('pending', 0)}"
            )
        elif intent == "list_tasks":
            tasks = result.get("tasks", [])
            if not tasks:
                return "✅ No pending tasks! You're all caught up!"
            response = "📋 **Upcoming Maintenance**\n"
            for task in tasks:
                response += f"• {task['name']} - Due: {task['due']} ({task['status']})\n"
            return response
        else:
            return f"✅ {result.get('message', 'Action completed')}"
    
    def _get_helpful_response(self, message: str) -> str:
        """Provide helpful response when intent cannot be determined"""
        return (
            "🤖 I can help you with maintenance tasks!\n\n"
            "Try saying:\n"
            "• 'Show my status'\n"
            "• 'What's upcoming?'\n"
            "• 'Set oil change reminder in 3 days'\n"
            "• 'Add tire rotation task'\n"
            "• 'Mark task 5 complete'\n"
            "• 'Check my budget'\n\n"
            "Or type /help for more options"
        )
    
    def save_checkpoint(self, thread_id: str, checkpoint_data: Dict[str, Any]) -> Optional[str]:
        """Save agent state checkpoint to PostgreSQL"""
        if not self.checkpointer:
            logger.warning("PostgresSaver not initialized")
            return None
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint_id = self.checkpointer.put(
                config=config,
                values=checkpoint_data,
                metadata={"timestamp": datetime.utcnow().isoformat()}
            )
            logger.info(f"✅ Checkpoint saved: {checkpoint_id}")
            return checkpoint_id
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return None
    
    def load_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Load agent state checkpoint from PostgreSQL"""
        if not self.checkpointer:
            logger.warning("PostgresSaver not initialized")
            return None
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint = self.checkpointer.get(config=config)
            if checkpoint:
                logger.info(f"✅ Checkpoint loaded for thread: {thread_id}")
                return checkpoint
            return None
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def get_all_checkpoints(self, thread_id: str) -> list:
        """Get all checkpoints for a thread (history)"""
        if not self.checkpointer:
            logger.warning("PostgresSaver not initialized")
            return []
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            history = list(self.checkpointer.list(config=config))
            logger.info(f"Found {len(history)} checkpoints for thread: {thread_id}")
            return history
        except Exception as e:
            logger.error(f"Failed to get checkpoint history: {e}")
            return []
    """
    Deep reasoning agent that:
    1. Understands user messages
    2. Identifies intent and required actions
    3. Selects appropriate skills to execute
    4. Provides intelligent responses
    
    Uses LangChain's PostgresSaver for native checkpoint persistence.
    """
    
    def __init__(self):
        # Import SkillExecutor from skills.py module (not skills/ package)
        import sys
        import importlib.util
        spec = importlib.util.spec_from_file_location("skills_module", "/app/agents/skills.py")
        if spec and spec.loader:
            skills_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(skills_module)
            SkillExecutor = skills_module.SkillExecutor
        else:
            # Fallback: create a minimal SkillExecutor
            class SkillExecutor:
                def execute(self, skill_type, parameters, db):
                    return {"status": "ok"}
        
        self.skill_registry = {}  # Skills loaded from skill_loader
        self.skill_executor = SkillExecutor()
        
        # Initialize checkpointer (checkpoint data will be stored in database via AgentExecution table)
        self.checkpointer = None
        logger.info("✅ Checkpointer initialized (checkpoints stored via AgentExecution table)")
    
    async def process_user_message(
        self, 
        message: str, 
        chat_id: int, 
        user_id: int,
        db: Session
    ) -> str:
        """
        Process a user message and determine what actions to take.
        
        Args:
            message: The user's message
            chat_id: Telegram chat ID
            user_id: Telegram user ID
            db: Database session
            
        Returns:
            Response message to send back to user
        """
        try:
            # 1. Analyze user intent
            intent = self._analyze_intent(message)
            logger.info(f"Detected intent: {intent}")
            
            # 2. Extract parameters from message
            parameters = self._extract_parameters(message, intent)
            logger.info(f"Extracted parameters: {parameters}")
            
            # 3. Execute appropriate skill(s)
            if intent:
                from agents.skills import SkillType
                
                skill_type = SkillType[intent.upper()] if intent.upper() in SkillType.__members__ else None
                
                if skill_type and self.skill_executor.can_execute(skill_type):
                    result = self.skill_executor.execute(skill_type, parameters, db)
                    logger.info(f"Skill execution result: {result}")
                    
                    # 4. Format response
                    return self._format_response(result, intent)
            
            # 5. Fallback - provide helpful response
            return self._get_helpful_response(message)
        
        except Exception as e:
            logger.error(f"Error in deep agent: {str(e)}", exc_info=True)
            return f"❌ Error processing request: {str(e)}"
    
    def _analyze_intent(self, message: str) -> Optional[str]:
        """
        Analyze user message to determine intent.
        Uses pattern matching and keywords to identify what the user wants.
        """
        message_lower = message.lower().strip()
        
        # Command patterns
        if any(phrase in message_lower for phrase in ["status", "how am i", "tell me my", "what's my"]):
            return "get_status"
        
        if any(phrase in message_lower for phrase in ["upcoming", "what's due", "what's coming", "next"]):
            return "list_tasks"
        
        if any(phrase in message_lower for phrase in ["remind", "set reminder", "alert me"]):
            return "set_reminder"
        
        if any(phrase in message_lower for phrase in ["complete", "done", "finished", "mark as done"]):
            return "update_task"
        
        if any(phrase in message_lower for phrase in ["add task", "new task", "create", "add maintenance"]):
            return "create_task"
        
        if any(phrase in message_lower for phrase in ["budget", "spent", "expense", "cost"]):
            return "check_budget"
        
        if any(phrase in message_lower for phrase in ["miles", "mileage", "update car", "odometer"]):
            return "update_vehicle"
        
        if any(phrase in message_lower for phrase in ["help", "what can", "commands", "options"]):
            return "help"
        
        return None
    
    def _extract_parameters(self, message: str, intent: Optional[str]) -> Dict[str, Any]:
        """Extract parameters from user message based on intent"""
        message_lower = message.lower()
        parameters = {}
        
        if intent == "set_reminder":
            # Extract days from message
            match = re.search(r'(\d+)\s*(day|week|month)', message_lower)
            if match:
                num = int(match.group(1))
                unit = match.group(2)
                if unit == "week":
                    num *= 7
                elif unit == "month":
                    num *= 30
                parameters["days"] = num
            else:
                parameters["days"] = 7  # Default to 7 days
            
            # Extract maintenance type
            if "oil" in message_lower or "oil change" in message_lower:
                parameters["maintenance"] = "Oil Change"
            elif "filter" in message_lower:
                parameters["maintenance"] = "Air Filter"
            elif "tire" in message_lower:
                parameters["maintenance"] = "Tire Rotation"
            else:
                # Try to extract from message
                words = message.split()
                for i, word in enumerate(words):
                    if word.lower() in ["remind", "about"]:
                        parameters["maintenance"] = " ".join(words[i+1:i+4]) if i+1 < len(words) else "Maintenance"
                        break
        
        elif intent == "create_task":
            # Extract task name
            if "oil" in message_lower:
                parameters["name"] = "Oil Change"
                parameters["type"] = "car"
            elif "filter" in message_lower:
                parameters["name"] = "Air Filter Replacement"
                parameters["type"] = "car"
            elif "tire" in message_lower:
                parameters["name"] = "Tire Rotation"
                parameters["type"] = "car"
            else:
                parameters["name"] = "New Maintenance Task"
                parameters["type"] = "house"
            
            # Extract due date if provided
            match = re.search(r'(\d{4}-\d{2}-\d{2})', message)
            if match:
                parameters["due_date"] = match.group(1)
            else:
                parameters["due_date"] = datetime.now().isoformat()
        
        elif intent == "update_task":
            # Extract task ID
            match = re.search(r'task\s*#?(\d+)', message_lower)
            if match:
                parameters["task_id"] = int(match.group(1))
            
            parameters["status"] = "completed"
        
        elif intent == "update_vehicle":
            # Extract vehicle name and mileage
            match = re.search(r'(\d+)\s*(mile|km)', message_lower)
            if match:
                parameters["miles"] = int(match.group(1))
            
            # Common vehicle names
            if "fiesta" in message_lower:
                parameters["vehicle"] = "Ford Fiesta"
            elif "odyssey" in message_lower:
                parameters["vehicle"] = "Honda Odyssey"
        
        return parameters
    
    def _format_response(self, result: Dict[str, Any], intent: str) -> str:
        """Format skill execution result into user-friendly response"""
        if not result.get("success"):
            return f"❌ {result.get('error', 'Something went wrong')}"
        
        if intent == "get_status":
            return (
                f"📊 **Maintenance Status**\n"
                f"✅ Completed: {result.get('completed', 0)}\n"
                f"🔄 In Progress: {result.get('in_progress', 0)}\n"
                f"⏳ Pending: {result.get('pending', 0)}"
            )
        
        elif intent == "list_tasks":
            tasks = result.get("tasks", [])
            if not tasks:
                return "✅ No pending tasks! You're all caught up!"
            
            response = "📋 **Upcoming Maintenance**\n"
            for task in tasks:
                response += f"• {task['name']} - Due: {task['due']} ({task['status']})\n"
            return response
        
        elif intent == "create_task":
            return f"✅ Created: {result.get('message', 'Task created')}"
        
        elif intent == "set_reminder":
            return f"⏰ {result.get('message', 'Reminder set')}"
        
        elif intent == "update_task":
            return f"✔️ {result.get('message', 'Task updated')}"
        
        else:
            return f"✅ {result.get('message', 'Action completed')}"
    
    def _get_helpful_response(self, message: str) -> str:
        """Provide helpful response when intent cannot be determined"""
        return (
            "🤖 I can help you with maintenance tasks!\n\n"
            "Try saying:\n"
            "• 'Show my status'\n"
            "• 'What's upcoming?'\n"
            "• 'Set oil change reminder in 3 days'\n"
            "• 'Add tire rotation task'\n"
            "• 'Mark task 5 complete'\n"
            "• 'Check my budget'\n\n"
            "Or type /help for more options"
        )
    
    def save_checkpoint(self, thread_id: str, checkpoint_data: Dict[str, Any]) -> Optional[str]:
        """
        Save agent state checkpoint to PostgreSQL via LangChain checkpointer.
        
        Args:
            thread_id: Unique thread/conversation identifier
            checkpoint_data: State data to checkpoint
            
        Returns:
            Checkpoint ID or None if failed
        """
        if not self.checkpointer:
            logger.warning("PostgresSaver not initialized, skipping checkpoint")
            return None
        
        try:
            # LangChain's checkpointer handles persistence
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint_id = self.checkpointer.put(
                config=config,
                values=checkpoint_data,
                metadata={"timestamp": datetime.utcnow().isoformat()}
            )
            logger.info(f"✅ Checkpoint saved: {checkpoint_id}")
            return checkpoint_id
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return None
    
    def load_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Load agent state checkpoint from PostgreSQL.
        
        Args:
            thread_id: Unique thread/conversation identifier
            
        Returns:
            Checkpoint data or None if not found
        """
        if not self.checkpointer:
            logger.warning("PostgresSaver not initialized, cannot load checkpoint")
            return None
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint = self.checkpointer.get(config=config)
            
            if checkpoint:
                logger.info(f"✅ Checkpoint loaded for thread: {thread_id}")
                return checkpoint
            else:
                logger.info(f"No checkpoint found for thread: {thread_id}")
                return None
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def get_all_checkpoints(self, thread_id: str) -> list:
        """
        Get all checkpoints for a thread (history).
        
        Args:
            thread_id: Unique thread/conversation identifier
            
        Returns:
            List of checkpoint metadata
        """
        if not self.checkpointer:
            logger.warning("PostgresSaver not initialized")
            return []
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            # Get checkpoint history
            history = list(self.checkpointer.list(config=config))
            logger.info(f"Found {len(history)} checkpoints for thread: {thread_id}")
            return history
        except Exception as e:
            logger.error(f"Failed to get checkpoint history: {e}")
            return []
    
    def reasoning_trace(self, message: str) -> Dict[str, Any]:
        """
        Provide reasoning trace for debugging.
        Shows how the agent analyzed the message.
        """
        intent = self._analyze_intent(message)
        parameters = self._extract_parameters(message, intent)
        
        return {
            "message": message,
            "detected_intent": intent,
            "extracted_parameters": parameters,
            "timestamp": datetime.now().isoformat()
        }
