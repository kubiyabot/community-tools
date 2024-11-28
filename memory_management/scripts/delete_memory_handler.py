import os
from mem0 import Memory

def delete_memory(memory_id):
    # Retrieve Mem0 configuration from environment variables
    uri = os.environ["NEO4J_URI"]
    username = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]
    user_email = os.environ["KUBIYA_USER_EMAIL"]
    user_org = os.environ["KUBIYA_USER_ORG"]

    # Build the Mem0 configuration
    config = {
        "graph_store": {
            "provider": "neo4j",
            "config": {
                "url": uri,
                "username": username,
                "password": password,
            }
        },
        "version": "v1.1"
    }

    # Instantiate the Memory client
    m = Memory.from_config(config_dict=config)

    # Use org.user_email as user_id
    user_id = f"{user_org}.{user_email}"

    # Delete the memory
    success = m.delete(memory_id=memory_id)

    if success:
        print("🗑️ Memory deleted successfully.")
    else:
        print("🚫 Memory not found or you do not have permission to delete it.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: delete_memory_handler.py <memory_id>")
        sys.exit(1)
    memory_id = sys.argv[1]
    delete_memory(memory_id) 