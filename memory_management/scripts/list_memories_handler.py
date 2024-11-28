import os
import json
from mem0 import Memory

def list_memories(tags=None):
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

    # Get all memories for the user
    memories = m.get_all(user_id=user_id)

    # Filter memories by tags if provided
    if tags:
        tag_set = set(tags)
        memories = [mem for mem in memories if tag_set.issubset(set(mem.get('metadata', {}).get('tags', [])))]

    if not memories:
        print("📭 No stored preferences found.")
    else:
        print(f"🧠 Stored preferences for {user_email}:\n")
        for mem in memories:
            tags = mem.get('metadata', {}).get('tags', [])
            print(f"ID: {mem['memory_id']}, Preference: {mem['data']}, Tags: {tags}, Timestamp: {mem['timestamp']}")

if __name__ == "__main__":
    import sys
    tags = json.loads(sys.argv[1]) if len(sys.argv) > 1 else None
    list_memories(tags) 