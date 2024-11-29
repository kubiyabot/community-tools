import sys
import json
from mem0 import Memory
from typing import Optional, List, Union
import os

# Add scripts directory to Python path for config import
scripts_dir = os.path.dirname(os.path.abspath(__file__))
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from config import MemoryConfig

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

        # Get configuration with optional custom prompt
        config = MemoryConfig.get_neo4j_config(custom_prompt)
        
        # Initialize Memory client
        m = Memory.from_config(config_dict=config)
        
        # Get user ID
        user_id = MemoryConfig.get_user_id()

        # Add the memory with tags
        metadata = {"tags": tags} if tags else {}
        result = m.add(memory_content, user_id=user_id, metadata=metadata)
        
        # Print success message with extracted entities if available
        print("🧠 User preference added successfully.")
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
        
        # Validate and parse tags
        tags = validate_tags(tags_str) if tags_str else None
        
        add_memory(memory_content, tags, custom_prompt)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1) 