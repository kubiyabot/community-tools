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

class DeleteMemoryTool(MemoryManagementTool):
    def __init__(self):
        memory_args = [
            Arg(
                name="memory_id",
                type="str",
                description="""ID of the memory to remove (use list_memories to find IDs).
                Example: "bf4d4092-cf91-4181-bfeb-b6fa2ed3061b""",
                required=True
            )
        ]

        super().__init__(
            name="delete_memory",
            description="""Remove outdated or irrelevant conversation points.

WHEN TO USE:
- When switching to a new topic
- If incorrect information was saved
- To remove resolved discussion points

⚠️ Check list_memories first to get the correct ID""",
            content="""#!/bin/sh
# Create Python script
cat > /tmp/delete_memory.py << 'EOL'
import os
import sys
from mem0 import MemoryClient

def delete_memory(memory_id):
    try:
        # Initialize client
        client = MemoryClient(api_key=os.environ["MEM0_API_KEY"])
        
        # Get user ID
        user_id = f"{os.environ['KUBIYA_USER_ORG']}.{os.environ['KUBIYA_USER_EMAIL']}"
        
        # Delete memory
        success = client.delete(memory_id)
        
        if success:
            print("✅ Memory deleted successfully")
        else:
            print("⚠️ Memory not found or you don't have permission to delete it")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    delete_memory("{{ .memory_id }}")
EOL

# Execute the Python script
python3 /tmp/delete_memory.py
""",
            args=memory_args
        )

# Create and register the tool
delete_memory_tool = DeleteMemoryTool()
tool_registry.register("memory_management", delete_memory_tool)

__all__ = ["delete_memory_tool", "DeleteMemoryTool"] 