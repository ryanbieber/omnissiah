"""Tool registry and execution system for agent skills.

Skills can define and use tools to execute CLI commands, call APIs, and run scripts.
This system manages tool discovery, validation, and execution with safety guardrails.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class Tool:
    """Represents an executable tool that skills can use."""
    
    def __init__(
        self,
        name: str,
        description: str,
        script_path: str,
        parameters: Dict[str, Dict[str, Any]],
        timeout_seconds: int = 30,
        enabled: bool = True
    ):
        """
        Initialize a tool.
        
        Args:
            name: Tool name (e.g., 'weather_check')
            description: What the tool does
            script_path: Path to executable script
            parameters: Parameter definitions
            timeout_seconds: Max execution time
            enabled: Whether tool is available
        """
        self.name = name
        self.description = description
        self.script_path = Path(script_path)
        self.parameters = parameters
        self.timeout_seconds = timeout_seconds
        self.enabled = enabled
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for LLM definitions."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "enabled": self.enabled
        }


class ToolRegistry:
    """Registry of available tools for skills."""
    
    def __init__(self):
        """Initialize empty registry."""
        self.tools: Dict[str, Tool] = {}
        self._load_lawncare_tools()
        self._load_car_tools()
        self._load_house_tools()
    
    def register_tool(self, tool: Tool) -> None:
        """Register a new tool."""
        self.tools[tool.name] = tool
        logger.info(f"✅ Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> List[Tool]:
        """List all tools, optionally filtered by category."""
        return list(self.tools.values())
    
    def get_tool_definitions_for_llm(self) -> List[Dict]:
        """Get tool definitions formatted for LLM."""
        return [tool.to_dict() for tool in self.tools.values() if tool.enabled]
    
    def _load_lawncare_tools(self) -> None:
        """Load tools for lawncare skill."""
        skills_dir = Path(__file__).parent / "skills" / "lawncare" / "scripts"
        
        weather_tool = Tool(
            name="weather_check",
            description="Check weather conditions to inform lawn care decisions. Returns temperature, precipitation, humidity forecast.",
            script_path=str(skills_dir / "weather_check.py"),
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location (default: Waverly, Iowa)"
                    },
                    "days_ahead": {
                        "type": "integer",
                        "description": "Days to forecast (default: 3)"
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Metrics to check: precipitation, temperature, humidity"
                    }
                }
            },
            timeout_seconds=15
        )
        self.register_tool(weather_tool)
        
        fertilizer_tool = Tool(
            name="fertilizer_calculator",
            description="Calculate optimal nitrogen rates and product recommendations based on lawn size, grass type, and season.",
            script_path=str(skills_dir / "fertilizer_calculator.py"),
            parameters={
                "type": "object",
                "properties": {
                    "lawn_size_sqft": {
                        "type": "integer",
                        "description": "Lawn size in square feet"
                    },
                    "grass_type": {
                        "type": "string",
                        "enum": ["cool-season", "warm-season"],
                        "description": "Type of grass (default: cool-season)"
                    },
                    "season": {
                        "type": "string",
                        "enum": ["spring", "summer", "early_fall", "fall"],
                        "description": "Current season for application timing"
                    },
                    "soil_test": {
                        "type": "object",
                        "description": "Optional soil test results"
                    }
                },
                "required": ["lawn_size_sqft"]
            },
            timeout_seconds=10
        )
        self.register_tool(fertilizer_tool)
        
        watering_tool = Tool(
            name="watering_decision",
            description="Determine if lawn needs watering based on soil type, weather, and recent precipitation.",
            script_path=str(skills_dir / "watering_decision.py"),
            parameters={
                "type": "object",
                "properties": {
                    "lawn_size_sqft": {
                        "type": "integer",
                        "description": "Lawn size in square feet"
                    },
                    "soil_type": {
                        "type": "string",
                        "enum": ["clay", "loam", "sand"],
                        "description": "Type of soil (default: loam)"
                    },
                    "last_watered_hours": {
                        "type": "integer",
                        "description": "Hours since last watering (default: 72)"
                    },
                    "last_rainfall_inches": {
                        "type": "number",
                        "description": "Recent rainfall amount (default: 0)"
                    },
                    "last_rainfall_hours": {
                        "type": "integer",
                        "description": "Hours since last rain (default: 96)"
                    }
                },
                "required": ["lawn_size_sqft"]
            },
            timeout_seconds=10
        )
        self.register_tool(watering_tool)
    
    def _load_car_tools(self) -> None:
        """Load tools for car maintenance skill."""
        # Placeholder for future car maintenance tools
        pass
    
    def _load_house_tools(self) -> None:
        """Load tools for house maintenance skill."""
        # Placeholder for future house maintenance tools
        pass


class ToolExecutor:
    """Executes tools safely with subprocess management."""
    
    def __init__(self, tool_registry: ToolRegistry):
        """Initialize executor with registry."""
        self.registry = tool_registry
    
    def execute(
        self,
        tool_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a tool with given parameters.
        
        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool parameters
        
        Returns:
            Execution result with output or error
        """
        tool = self.registry.get_tool(tool_name)
        
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "tool": tool_name
            }
        
        if not tool.enabled:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' is disabled",
                "tool": tool_name
            }
        
        if not tool.script_path.exists():
            return {
                "success": False,
                "error": f"Tool script not found: {tool.script_path}",
                "tool": tool_name
            }
        
        try:
            # Build command
            cmd = [sys.executable, str(tool.script_path)]
            
            # Add parameters as arguments
            for key, value in kwargs.items():
                if isinstance(value, (list, dict)):
                    cmd.append(json.dumps(value))
                else:
                    cmd.append(str(value))
            
            logger.info(f"Executing tool '{tool_name}': {' '.join(cmd[:3])}...")
            
            # Execute with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=tool.timeout_seconds,
                check=False
            )
            
            # Parse output
            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout)
                    logger.info(f"✅ Tool '{tool_name}' executed successfully")
                    return {
                        "success": True,
                        "tool": tool_name,
                        "output": output
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "tool": tool_name,
                        "output": result.stdout
                    }
            else:
                logger.error(f"Tool '{tool_name}' failed: {result.stderr}")
                return {
                    "success": False,
                    "tool": tool_name,
                    "error": result.stderr or "Unknown error",
                    "returncode": result.returncode
                }
        
        except subprocess.TimeoutExpired:
            logger.error(f"Tool '{tool_name}' timed out after {tool.timeout_seconds}s")
            return {
                "success": False,
                "tool": tool_name,
                "error": f"Tool execution timed out after {tool.timeout_seconds} seconds"
            }
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution error: {e}")
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }


# Singleton instances
_tool_registry: Optional[ToolRegistry] = None
_tool_executor: Optional[ToolExecutor] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create tool registry singleton."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def get_tool_executor() -> ToolExecutor:
    """Get or create tool executor singleton."""
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutor(get_tool_registry())
    return _tool_executor


def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Execute a tool with parameters."""
    executor = get_tool_executor()
    return executor.execute(tool_name, **kwargs)
