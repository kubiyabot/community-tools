import os
import sys
from mem0 import MemoryClient

def search_memories(query: str) -> None:
    """Search memories using the provided query."""
    try:
        # Initialize Memory client
        client = MemoryClient(api_key=os.environ["MEM0_API_KEY"])
        
        # Get user ID
        user_id = f"{os.environ['KUBIYA_USER_ORG']}.{os.environ['KUBIYA_USER_EMAIL']}"

        print(f"🔍 Searching memories for: {query}")
        
        # Search memories with v1.1 format
        results = client.search(query, user_id=user_id, output_format="v1.1")
        
        if not results or not results.get('results'):
            print("No matching memories found.")
            return
            
        print("\n✨ Found matching memories:\n")
        for memory in results['results']:
            print(f"📌 {memory.get('content', '')}")
            if 'metadata' in memory and 'tags' in memory['metadata']:
                print(f"   Tags: {', '.join(memory['metadata']['tags'])}")
            print(f"   Score: {memory.get('score', 0):.2f}")
            print()

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: search_memories_handler.py <query>")
        sys.exit(1)
    search_memories(sys.argv[1])