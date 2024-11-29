import os
import sys
from mem0 import Memory
from typing import Optional, Dict, Any, List

# Add scripts directory to Python path for config import
scripts_dir = os.path.dirname(os.path.abspath(__file__))
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from config import MemoryConfig

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

        try:
            # Use mem0's search functionality
            search_results = m.search(query=search_query, user_id=user_id)
            
            if search_results and isinstance(search_results, dict):
                memories = [
                    MemoryConfig.format_memory_response(mem) 
                    for mem in search_results.get('results', [])
                ]
            else:
                memories = []
                
        except Exception as e:
            print(f"⚠️ Search failed: {str(e)}")
            return

        if not memories:
            print("🤔 No matching preferences found.")
            print("\n💡 Tips for better search:")
            print("- Try using different keywords")
            print("- Check for typos")
            print("- Use broader terms")
            print("\n📋 Use 'load_memories' to see all your preferences")
            return

        print(f"\n✨ Found {len(memories)} matching preferences:\n")
        for mem in memories:
            tags = mem['metadata'].get('tags', [])
            tags_str = f"[{', '.join(tags)}]" if tags else "[]"
            
            print(f"📌 {mem['content']}")
            print(f"   ID: {mem['memory_id']}")
            print(f"   Tags: {tags_str}")
            
            # Display extracted entities if available
            if mem.get('entities'):
                print(f"   Entities: {', '.join(str(e) for e in mem['entities'])}")
            
            print(f"   Added: {mem['timestamp']}\n")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: find_preference_handler.py <search_query>")
        sys.exit(1)
    find_preference(sys.argv[1]) 