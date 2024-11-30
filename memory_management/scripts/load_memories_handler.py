import os
import sys
from mem0 import MemoryClient
from typing import Dict, Any, List

def load_memories() -> None:
    """Load and display all stored preferences for the current user."""
    try:
        # Initialize Memory client with API key from environment
        client = MemoryClient(api_key=os.environ["MEM0_API_KEY"])
        
        # Get user ID
        user_id = f"{os.environ['KUBIYA_USER_ORG']}.{os.environ['KUBIYA_USER_EMAIL']}"

        print("🔄 Loading your preferences... 🧠")

        # Get all memories for the user
        raw_memories = client.get_all(user_id=user_id)
        
        # Handle different response formats
        memories = (raw_memories if isinstance(raw_memories, list) 
                   else raw_memories.get('memories', []))

        if not memories:
            print("📭 No stored preferences found. Use the add_memory tool to store your first preference!")
            return

        print(f"🎉 Found {len(memories)} stored preferences:\n")
        
        # Group memories by tags for better organization
        tag_groups = {}
        untagged = []
        
        for mem in memories:
            tags = mem.get('metadata', {}).get('tags', [])
            if tags:
                for tag in tags:
                    if tag not in tag_groups:
                        tag_groups[tag] = []
                    tag_groups[tag].append(mem)
            else:
                untagged.append(mem)

        # Print grouped memories
        if tag_groups:
            print("📑 Grouped by categories:")
            for tag, mems in tag_groups.items():
                print(f"\n🏷️ {tag.upper()}:")
                for mem in mems:
                    print(f"  📌 {mem.get('content', mem.get('data', ''))}")
                    print(f"     ID: {mem.get('id', 'unknown')}")
                    print(f"     Added: {mem.get('timestamp', 'unknown')}\n")

        # Print untagged memories
        if untagged:
            print("\n📋 Other preferences:")
            for mem in untagged:
                print(f"  📌 {mem.get('content', mem.get('data', ''))}")
                print(f"     ID: {mem.get('id', 'unknown')}")
                print(f"     Added: {mem.get('timestamp', 'unknown')}\n")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    load_memories() 