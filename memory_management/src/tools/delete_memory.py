import inspect
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.registry import tool_registry
from .base import MemoryManagementTool
from ..utils import get_script_files

class DeleteMemoryTool(MemoryManagementTool):
    def __init__(self):
        try:
            import mem0
            description = "Delete memories with specified tags"
        except ImportError:
            description = "Delete memories with specified tags (mem0 package will be installed at runtime)"

        # Get memory configuration
        memory_config = tool_registry.get_tool_config("memory")
        backend_type = memory_config.get('backend', 'hosted') if memory_config else 'hosted'

        # Define base environment variables and secrets
        env = ["KUBIYA_USER_EMAIL", "KUBIYA_USER_ORG"]
        secrets = []

        # Add mode-specific requirements
        if backend_type == 'hosted':
            secrets.append("MEM0_API_KEY")
        elif backend_type == 'neo4j':
            env.extend(["NEO4J_URI", "NEO4J_USER"])
            secrets.append("NEO4J_PASSWORD")

        super().__init__(
            name="delete_memory",
            description=description,
            content="""
try:
    import mem0
    from mem0.memory import Memory
    
    # Initialize memory
    memory = Memory()
    
    # Delete memories with tags
    memory.delete(tags)
    print("✅ Successfully deleted memories with specified tags")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    exit(1)
""",
            env=env,
            secrets=secrets
        )

# Register the tool
tool_registry.register("memory_management", DeleteMemoryTool())

__all__ = ["DeleteMemoryTool"] 