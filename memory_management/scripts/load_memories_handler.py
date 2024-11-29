import os
import sys
from mem0 import Memory
from typing import Dict, Any, List

# Add scripts directory to Python path for config import
scripts_dir = os.path.dirname(os.path.abspath(__file__))
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from config import MemoryConfig

def format_memory(memory: Dict[str, Any]) -> Dict[str, Any]:
    """Format memory data consistently regardless of response format."""
    if isinstance(memory, str):
        # Handle case where memory is just a string
        return {
            'data': memory,
            'memory_id': 'unknown',
            'timestamp': 'unknown',
            'metadata': {'tags': []}
        }
    elif isinstance(memory, dict):
        # Handle dictionary format
        return {
            'data': memory.get('data', memory.get('content', memory.get('memory', ''))),
            'memory_id': memory.get('memory_id', memory.get('id', 'unknown')),
            'timestamp': memory.get('timestamp', memory.get('created_at', 'unknown')),
            'metadata': memory.get('metadata', {'tags': []})
        }
    else:
        raise ValueError(f"Unexpected memory format: {type(memory)}")

def load_memories() -> None:
    """Load and display all stored preferences for the current user."""
    try:
        # Get configuration
        config = MemoryConfig.get_neo4j_config()
        
        # Initialize Memory client
        m = Memory.from_config(config_dict=config)
        
        # Get user ID
        user_id = MemoryConfig.get_user_id()

        print("🔄 Loading your preferences... 🧠")

        # Get all memories for the user
        raw_memories = m.get_all(user_id=user_id)
        
        # Handle different response formats
        if isinstance(raw_memories, dict):
            memories = [format_memory(mem) for mem in raw_memories.get('memories', [])]
        elif isinstance(raw_memories, list):
            memories = [format_memory(mem) for mem in raw_memories]
        else:
            memories = []

        if not memories:
            print("📭 No stored preferences found. Use the add_memory tool to store your first preference!")
            return

        print(f"🎉 Found {len(memories)} stored preferences:\n")
        
        # Group memories by tags for better organization
        tag_groups = {}
        untagged = []
        
        for mem in memories:
            formatted_mem = format_memory(mem)
            tags = formatted_mem['metadata'].get('tags', [])
            if tags:
                for tag in tags:
                    if tag not in tag_groups:
                        tag_groups[tag] = []
                    tag_groups[tag].append(formatted_mem)
            else:
                untagged.append(formatted_mem)

        # Print grouped memories
        if tag_groups:
            print("📑 Grouped by categories:")
            for tag, mems in tag_groups.items():
                print(f"\n🏷️ {tag.upper()}:")
                for mem in mems:
                    print(f"  📌 {mem['data']}")
                    print(f"     ID: {mem['memory_id']}")
                    print(f"     Added: {mem['timestamp']}\n")

        # Print untagged memories
        if untagged:
            print("\n📋 Other preferences:")
            for mem in untagged:
                print(f"  📌 {mem['data']}")
                print(f"     ID: {mem['memory_id']}")
                print(f"     Added: {mem['timestamp']}\n")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    load_memories() 