import os
import sys
from mem0 import MemoryClient
from typing import Optional, Dict, Any, List

def find_preference(search_query: str) -> None:
    """
    Search for specific preferences using the provided query.
    
    Args:
        search_query: Text to search for in preferences
    """
    try:
        if not search_query.strip():
            raise ValueError("Search query cannot be empty")

        # Initialize Memory client with API key from environment
        client = MemoryClient(api_key=os.environ["MEM0_API_KEY"])
        
        # Get user ID
        user_id = f"{os.environ['KUBIYA_USER_ORG']}.{os.environ['KUBIYA_USER_EMAIL']}"

        print(f"🔍 Searching for preferences matching '{search_query}'...")

        try:
            # Use mem0's search functionality
            search_results = client.search(query=search_query, user_id=user_id)
            
            if search_results and isinstance(search_results, dict):
                memories = search_results.get('results', [])
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
            tags = mem.get('metadata', {}).get('tags', [])
            tags_str = f"[{', '.join(tags)}]" if tags else "[]"
            
            print(f"📌 {mem.get('content', mem.get('data', ''))}")
            print(f"   ID: {mem.get('id', 'unknown')}")
            print(f"   Tags: {tags_str}")
            
            # Display extracted entities if available
            if 'entities' in mem:
                print(f"   Entities: {', '.join(str(e) for e in mem['entities'])}")
            
            print(f"   Added: {mem.get('timestamp', 'unknown')}\n")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: find_preference_handler.py <search_query>")
        sys.exit(1)
    find_preference(sys.argv[1]) 