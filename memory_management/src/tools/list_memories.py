import sys
from pathlib import Path
from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.registry import tool_registry
from .base import MemoryManagementTool

class ListMemoriesTool(MemoryManagementTool):
    def __init__(self):
        memory_args = [
            Arg(
                name="filter",
                type="str",
                description="""Filter to find specific context from our conversation.
                
                Examples:
                - "kubernetes" - find all Kubernetes-related context
                - "deployment error" - find deployment issues
                - "preferences" - find user preferences
                - Leave empty to see all recent context""",
                required=False,
                default=""
            ),
            Arg(
                name="limit",
                type="str",
                description="Number of most recent memories to show (default: 10)",
                required=False,
                default="10"
            )
        ]

        super().__init__(
            name="list_memories",
            description="""🔍 Find relevant context from our conversation.

WHEN TO USE:
- Before suggesting solutions: "filter: error" to see previous issues
- To continue a topic: "filter: kubernetes" to recall Kubernetes discussion
- To check preferences: "filter: prefer" or "filter: settings"
- Leave filter empty to see all recent context

The tool searches both content and tags to find relevant information.""",
            content="""#!/bin/sh
# Create Python script
cat > /tmp/list_memories.py << 'EOL'
import os
import sys
import json
from mem0 import MemoryClient

def list_memories(filter_text, limit):
    try:
        # Initialize client
        client = MemoryClient(api_key=os.environ["MEM0_API_KEY"])
        
        # Get user ID
        user_id = f"{os.environ['KUBIYA_USER_ORG']}.{os.environ['KUBIYA_USER_EMAIL']}"
        
        # Handle default values
        filter_text = filter_text if filter_text != "<no value>" else ""
        try:
            limit = int(limit) if limit != "<no value>" else 10
        except ValueError:
            limit = 10
        
        # Build filters
        filters = {
            "AND": [{"user_id": user_id}]
        }
        
        if filter_text:
            filters["AND"].append({
                "OR": [
                    {"content": {"contains": filter_text}},
                    {"metadata.tags": {"contains": filter_text}}
                ]
            })
        
        # Get memories with filters
        memories = client.get_all(
            version="v2",
            filters=filters,
            page=1,
            page_size=limit
        )
        
        # Handle both list and dict response formats
        if isinstance(memories, dict):
            if 'results' in memories:
                memories_list = memories['results']
            else:
                memories_list = memories.get('memories', [])
        else:
            memories_list = memories if isinstance(memories, list) else []
        
        if not memories_list:
            print("📭 No relevant context found")
            sys.exit(0)
            
        print(f"🧠 Found {len(memories_list)} relevant items:")
        for memory in memories_list:
            # Get memory content
            content = memory.get('content', '') or memory.get('memory', '')
            
            # Get metadata and categories
            metadata = memory.get('metadata', {}) or {}
            categories = memory.get('categories', [])
            tags = metadata.get('tags', []) if metadata else []
            
            # Combine all tags and categories
            all_tags = list(set(tags + categories))
            tags_str = f"[{', '.join(all_tags)}]" if all_tags else ""
            
            # Get timestamps
            created = memory.get('created_at', '').split('T')[0]
            
            # Print formatted memory
            print(f"📌 {content}")
            if tags_str:
                print(f"   Tags: {tags_str}")
            if created:
                print(f"   Added: {created}")
            print()

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    list_memories("{{ .filter }}", "{{ .limit }}")
EOL

# Execute the Python script
python3 /tmp/list_memories.py
""",
            args=memory_args
        )

# Create and register the tool
list_memories_tool = ListMemoriesTool()
tool_registry.register("memory_management", list_memories_tool)

__all__ = ["ListMemoriesTool", "list_memories_tool"] 