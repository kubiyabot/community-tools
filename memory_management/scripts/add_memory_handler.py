import sys
import json
import os
from mem0 import Memory, MemoryClient
from typing import Optional, List, Union

def validate_tags(tags_str: Optional[str]) -> Optional[List[str]]:
    """Validate and parse tags JSON string."""
    if not tags_str:
        return None
    try:
        tags = json.loads(tags_str)
        if not isinstance(tags, list):
            raise ValueError("Tags must be a JSON array")
        if not all(isinstance(tag, str) for tag in tags):
            raise ValueError("All tags must be strings")
        return tags
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format for tags")

def get_memory_client():
    """Get appropriate memory client based on environment."""
    if all(os.environ.get(var) for var in ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]):
        # Use Memory with Neo4j config
        config = {
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": os.environ["NEO4J_URI"],
                    "username": os.environ["NEO4J_USER"],
                    "password": os.environ["NEO4J_PASSWORD"],
                }
            },
            "version": "v1.1"
        }
        return Memory.from_config(config_dict=config)
    else:
        # Use MemoryClient with API key
        return MemoryClient(api_key=os.environ["MEM0_API_KEY"])

def add_memory(
    memory_content: str, 
    tags: Optional[List[str]] = None,
    custom_prompt: Optional[str] = None
) -> None:
    """
    Add a memory with optional tags and custom prompt.
    
    Args:
        memory_content: The content to store in memory
        tags: Optional list of tags to categorize the memory
        custom_prompt: Optional custom prompt for entity extraction
    """
    try:
        if not memory_content or not isinstance(memory_content, str):
            raise ValueError("Memory content must be a non-empty string")

        # Get appropriate memory client
        client = get_memory_client()
        
        # Get user ID
        user_id = f"{os.environ['KUBIYA_USER_ORG']}.{os.environ['KUBIYA_USER_EMAIL']}"

        # Add the memory with tags
        metadata = {"tags": tags} if tags else {}
        
        # Format message for Mem0 if using MemoryClient
        if isinstance(client, MemoryClient):
            messages = [{"role": "user", "content": memory_content}]
            result = client.add(messages, user_id=user_id, metadata=metadata, output_format="v1.1")
        else:
            result = client.add(memory_content, user_id=user_id, metadata=metadata)
        
        print("🧠 Memory added successfully!")
        if result and "extracted_entities" in result:
            print("\n📊 Extracted Entities:")
            for entity in result["extracted_entities"]:
                print(f"- {entity}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            print("Usage: add_memory_handler.py <memory_content> [tags] [custom_prompt]")
            sys.exit(1)

        memory_content = sys.argv[1]
        tags_str = sys.argv[2] if len(sys.argv) > 2 else None
        custom_prompt = sys.argv[3] if len(sys.argv) > 3 else None
        
        tags = validate_tags(tags_str) if tags_str else None
        add_memory(memory_content, tags, custom_prompt)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1) 