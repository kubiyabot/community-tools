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
        memory_args = [
            Arg(
                name="memory_content",
                type="str",
                description='Important point to remember from our conversation. '
                          'Example: "Working on Kubernetes deployment issue in production"',
                required=True
            ),
            Arg(
                name="tags",
                type="str",
                description='Tags to categorize this memory. '
                          'Format: \'["tag1", "tag2"]\' or "tag1,tag2" or "tag1". '
                          'Example: "kubernetes,production"',
                required=True
            )
        ]

        super().__init__(
            name="add_memory",
            description="""Remember key points from our current conversation.

WHEN TO USE:
- To save important context for follow-up questions
- When discussing multiple related topics
- To track the main points of our discussion""",
            content="""#!/bin/sh
# Create Python script
cat > /tmp/add_memory.py << 'EOL'
import os
import sys
import json
from mem0 import MemoryClient

def add_memory(content, tags):
    try:
        # Initialize client
        client = MemoryClient(api_key=os.environ["MEM0_API_KEY"])
        
        # Get user ID
        user_id = f"{os.environ['KUBIYA_USER_ORG']}.{os.environ['KUBIYA_USER_EMAIL']}"
        
        # Process tags
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except json.JSONDecodeError:
                tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Add memory
        result = client.add(
            content,
            user_id=user_id,
            metadata={"tags": tags},
            output_format="v1.1"
        )
        
        print("✅ Successfully added memory")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    add_memory("{{ .memory_content }}", "{{ .tags }}")
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