import os
import sys
from mem0 import MemoryClient
from typing import Optional

def list_memories(search_filter: Optional[str] = None) -> None:
    """
    List all memories for the current user with optional search filtering.
    
    Args:
        search_filter: Optional text to filter memories (searches in content and tags)
    """
    try:
        # Initialize Memory client with API key from environment
        client = MemoryClient(api_key=os.environ["MEM0_API_KEY"])
        
        # Get user ID
        user_id = f"{os.environ['KUBIYA_USER_ORG']}.{os.environ['KUBIYA_USER_EMAIL']}"

        print("🔍 Scanning your memory bank... 🧠")

        # Get all memories for the user
        memories = client.get_all(user_id=user_id)

        if not memories:
            print("📭 No stored preferences found.")
            return

        # Filter memories if search_filter is provided
        if search_filter:
            filtered_memories = []
            search_terms = search_filter.lower().split()
            for mem in memories:
                content = mem.get('content', mem.get('data', '')).lower()
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
            print(f"📌 ID: {mem.get('id', 'unknown')}")
            print(f"   Content: {mem.get('content', mem.get('data', ''))}")
            print(f"   Tags: {tags_str}")
            print(f"   Added: {mem.get('timestamp', 'unknown')}\n")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    search_filter = sys.argv[1] if len(sys.argv) > 1 else None
    list_memories(search_filter) 