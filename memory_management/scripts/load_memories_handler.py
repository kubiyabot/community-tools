import os
from mem0 import Memory
from .config import MemoryConfig

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
        memories = m.get_all(user_id=user_id)

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