import os
from mem0 import Memory

def search_memories(query):
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

    # Search memories
    results = m.search(query=query, user_id=user_id)

    if not results['results']:
        print("🔍 No matching memories found.")
    else:
        print(f"🔍 Search results for '{query}':\n")
        for mem in results['results']:
            tags = mem.get('metadata', {}).get('tags', [])
            print(f"ID: {mem['id']}, Content: {mem['memory']}, Tags: {tags}, Score: {mem['score']}") 