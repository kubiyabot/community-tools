import sys
from pathlib import Path
from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.registry import tool_registry
from .base import MemoryManagementTool

class ListMemoriesTool(MemoryManagementTool):
    def __init__(self):
        memory_args = [
            Arg(
                name="page",
                type="str",
                description="Page number for viewing recent conversation history (start with '1')",
                required=False,
                default="1"
            ),
            Arg(
                name="page_size",
                type="str",
                description="Number of memories per page (default: 50)",
                required=False,
                default="50"
            )
        ]

        super().__init__(
            name="list_memories",
            description="""🎯 View what I remember from our current conversation.

WHEN TO USE:
- To check what I understood from our discussion
- Before asking follow-up questions
- To reference earlier points in the conversation""",
            content="""#!/bin/sh
# Create Python script
cat > /tmp/list_memories.py << 'EOL'
import os
import sys
import json
from mem0 import MemoryClient

def list_memories(page, page_size):
    try:
        # Initialize client
        client = MemoryClient(api_key=os.environ["MEM0_API_KEY"])
        
        # Get user ID
        user_id = f"{os.environ['KUBIYA_USER_ORG']}.{os.environ['KUBIYA_USER_EMAIL']}"
        
        # Get memories with pagination
        memories = client.get_all(
            user_id=user_id,
            page=int(page),
            page_size=int(page_size),
            output_format="v1.1"
        )
        
        if not memories.get('memories'):
            print("📭 No memories found")
            sys.exit(0)
            
        print(f"🧠 Found {len(memories['memories'])} memories:")
        for memory in memories['memories']:
            tags = memory.get('metadata', {}).get('tags', [])
            tags_str = f"[{', '.join(tags)}]" if tags else "[]"
            print(f"📌 ID: {memory.get('id', 'unknown')}")
            print(f"   Content: {memory.get('content', '')}")
            print(f"   Tags: {tags_str}")
            print(f"   Added: {memory.get('created_at', 'unknown')}\n")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    list_memories("{{ .page }}", "{{ .page_size }}")
EOL

# Execute the Python script
python3 /tmp/list_memories.py
""",
            args=memory_args
        )

# Create and register the tool
list_memories_tool = ListMemoriesTool()
tool_registry.register("memory_management", list_memories_tool)

__all__ = ["list_memories_tool", "ListMemoriesTool"] 