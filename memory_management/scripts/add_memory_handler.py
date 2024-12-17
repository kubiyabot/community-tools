#!/usr/bin/env python3
import os
import sys
import json
from typing import Optional, List, Union

def add_memory(content: str, tags: Optional[Union[str, List[str]]] = None, custom_prompt: Optional[str] = None) -> None:
    """Add a new memory with tags."""
    try:
        # Import mem0 at runtime
        try:
            from mem0 import MemoryClient
        except ImportError:
            print("❌ Error: mem0 package not installed. Installing required packages...")
            sys.exit(1)

        # Validate and process tags
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except json.JSONDecodeError:
                tags = [tag.strip() for tag in tags.split(',') if tag.strip()]

        # Initialize Memory client
        client = MemoryClient(api_key=os.environ["MEM0_API_KEY"])
        
        # Get user ID
        user_id = f"{os.environ['KUBIYA_USER_ORG']}.{os.environ['KUBIYA_USER_EMAIL']}"

        # Add memory
        result = client.add(
            content=content,
            user_id=user_id,
            tags=tags,
            custom_prompt=custom_prompt
        )

        print("✅ Successfully added memory")
        return result

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: add_memory_handler.py <content> [tags] [custom_prompt]")
        sys.exit(1)
        
    content = sys.argv[1]
    tags = sys.argv[2] if len(sys.argv) > 2 else None
    custom_prompt = sys.argv[3] if len(sys.argv) > 3 else None
    
    add_memory(content, tags, custom_prompt) 