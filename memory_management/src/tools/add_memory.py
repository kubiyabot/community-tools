import inspect
import sys
import os
from pathlib import Path
import json

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.registry import tool_registry

from .base import MemoryManagementTool

# Import all scripts from the scripts directory
scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
script_files = {}
for script_path in scripts_dir.glob("*.py"):
    with open(script_path, "r") as f:
        script_files[script_path.name] = f.read()

class AddMemoryTool(MemoryManagementTool):
    def __init__(self):
        try:
            import mem0
            description = "Add content to memory with specified tags"
        except ImportError:
            description = "Add content to memory with specified tags (mem0 package will be installed at runtime)"

        # Get memory configuration
        memory_config = tool_registry.get_tool_config("memory")
        backend_type = memory_config.get('backend', 'hosted') if memory_config else 'hosted'

        # Define base environment variables and secrets
        env = ["KUBIYA_USER_EMAIL", "KUBIYA_USER_ORG"]
        secrets = ["LLM_API_KEY"]  # Always needed for entity extraction

        # Add mode-specific requirements
        if backend_type == 'hosted':
            secrets.append("MEM0_API_KEY")
        elif backend_type == 'neo4j':
            env.extend(["NEO4J_URI", "NEO4J_USER"])
            secrets.append("NEO4J_PASSWORD")

        super().__init__(
            name="add_memory",
            description=description,
            content="""
try:
    import mem0
    from mem0.memory import Memory
    
    # Initialize memory
    memory = Memory()
    
    # Add content to memory
    memory.add(memory_content, tags)
    print("✅ Successfully added content to memory")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    exit(1)
""",
            env=env,
            secrets=secrets
        )

# Register the tool
tool_registry.register("memory_management", AddMemoryTool())

__all__ = ["AddMemoryTool"] 