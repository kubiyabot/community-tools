import os
from mem0 import Memory
from typing import Optional
from .config import MemoryConfig

def list_memories(search_filter: Optional[str] = None) -> None:
    """
    List all memories for the current user with optional search filtering.
    
    Args:
        search_filter: Optional text to filter memories (searches in content and tags)
    """
    try:
        # Get configuration
        config = MemoryConfig.get_neo4j_config()
        
        # Initialize Memory client
        m = Memory.from_config(config_dict=config)
        
        # Get user ID
        user_id = MemoryConfig.get_user_id()

        print("🔍 Scanning your memory bank... 🧠")

        # Get all memories for the user
        memories = m.get_all(user_id=user_id)

        if not memories:
            print("📭 No stored preferences found.")
            return

        # Filter memories if search_filter is provided
        if search_filter:
            filtered_memories = []
            search_terms = search_filter.lower().split()
            for mem in memories:
                content = mem['data'].lower()
                tags = [tag.lower() for tag in mem.get('metadata', {}).get('tags', [])]
                
                # Check if any search term is in content or tags
                if any(term in content or any(term in tag for tag in tags) 
                      for term in search_terms):
                    filtered_memories.append(mem)
            memories = filtered_memories

        if not memories:
            print(f"🔍 No preferences found matching '{search_filter}'")
            return

        print(f"🧠 Found {len(memories)} stored preferences:\n")
        for mem in memories:
            tags = mem.get('metadata', {}).get('tags', [])
            tags_str = f"[{', '.join(tags)}]" if tags else "[]"
            print(f"📌 ID: {mem['memory_id']}")
            print(f"   Content: {mem['data']}")
            print(f"   Tags: {tags_str}")
            print(f"   Added: {mem['timestamp']}\n")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    search_filter = sys.argv[1] if len(sys.argv) > 1 else None
    list_memories(search_filter) 