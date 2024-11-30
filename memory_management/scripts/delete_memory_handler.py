import os
import sys
from mem0 import MemoryClient

def delete_memory(memory_id: str) -> None:
    """Delete a memory by its ID."""
    try:
        # Initialize Memory client with API key from environment
        client = MemoryClient(api_key=os.environ["MEM0_API_KEY"])
        
        # Get user ID
        user_id = f"{os.environ['KUBIYA_USER_ORG']}.{os.environ['KUBIYA_USER_EMAIL']}"

        # Delete the memory
        success = client.delete(memory_id=memory_id)

        if success:
            print("🗑️ Memory deleted successfully.")
        else:
            print("🚫 Memory not found or you do not have permission to delete it.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: delete_memory_handler.py <memory_id>")
        sys.exit(1)
    memory_id = sys.argv[1]
    delete_memory(memory_id) 