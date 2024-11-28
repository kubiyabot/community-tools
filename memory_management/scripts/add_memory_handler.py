import os
import json
from mem0 import Memory

def add_memory(memory_content, tags=None):
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

    # Add the memory with tags
    metadata = {"tags": tags} if tags else {}
    m.add(memory_content, user_id=user_id, metadata=metadata)
    print("🧠 User preference added successfully.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: add_memory_handler.py <memory_content> [tags]")
        sys.exit(1)
    memory_content = sys.argv[1]
    tags = json.loads(sys.argv[2]) if len(sys.argv) > 2 else None
    add_memory(memory_content, tags) 