import os
from mem0 import Memory
from typing import Optional
from .config import MemoryConfig

def find_preference(search_query: str) -> None:
    """
    Search for specific preferences using the provided query.
    
    Args:
        search_query: Text to search for in preferences
    """
    try:
        if not search_query.strip():
            raise ValueError("Search query cannot be empty")

        # Get configuration
        config = MemoryConfig.get_neo4j_config()
        
        # Initialize Memory client
        m = Memory.from_config(config_dict=config)
        
        # Get user ID
        user_id = MemoryConfig.get_user_id()

        print(f"🔍 Searching for preferences matching '{search_query}'...")

        # Get all memories and filter them
        memories = m.get_all(user_id=user_id)
        
        if not memories:
            print("📭 No stored preferences found.")
            return

        # Perform search
        search_terms = search_query.lower().split()
        matches = []
        
        for mem in memories:
            content = mem['data'].lower()
            tags = [tag.lower() for tag in mem.get('metadata', {}).get('tags', [])]
            
            # Calculate match score based on number of matching terms
            score = sum(1 for term in search_terms if term in content or any(term in tag for tag in tags))
            
            if score > 0:
                matches.append((score, mem))

        if not matches:
            print("🤔 No matching preferences found.")
            print("\n💡 Tips for better search:")
            print("- Try using different keywords")
            print("- Check for typos")
            print("- Use broader terms")
            print("\n📋 Use 'load_memories' to see all your preferences")
            return

        # Sort by score (most relevant first)
        matches.sort(reverse=True, key=lambda x: x[0])
        
        print(f"\n✨ Found {len(matches)} matching preferences:\n")
        for score, mem in matches:
            tags = mem.get('metadata', {}).get('tags', [])
            tags_str = f"[{', '.join(tags)}]" if tags else "[]"
            
            print(f"📌 {mem['data']}")
            print(f"   ID: {mem['memory_id']}")
            print(f"   Tags: {tags_str}")
            print(f"   Added: {mem['timestamp']}\n")

    except ValueError as e:
        print(f"❌ {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: find_preference_handler.py <search_query>")
        sys.exit(1)
    find_preference(sys.argv[1]) 