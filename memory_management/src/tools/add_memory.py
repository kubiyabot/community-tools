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
        # Define memory arguments
        memory_args = [
            Arg(
                name="memory_content",
                type="str",
                description="The content to store in memory",
                required=True
            ),
            Arg(
                name="tags",
                type="str",
                description="""Tags to categorize the memory. Can be:
                - JSON array: '["tag1", "tag2"]'
                - Comma-separated: "tag1,tag2"
                - Single tag: "tag1" """,
                required=True
            ),
            Arg(
                name="custom_prompt",
                type="str",
                description="Optional custom prompt for entity extraction",
                required=False
            ),
        ]

        super().__init__(
            name="add_memory",
            description="Add content to memory with specified tags",
            content="""#!/bin/sh
# Create Python script
cat > /tmp/add_memory.py << 'EOL'
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
EOL

# Execute the Python script
python3 /tmp/add_memory.py
""",
            args=memory_args
        )

# Create and register the tool
add_memory_tool = AddMemoryTool()
tool_registry.register("memory_management", add_memory_tool)

__all__ = ["add_memory_tool", "AddMemoryTool"] 