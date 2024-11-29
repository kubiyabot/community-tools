import os
from typing import Optional, Dict, Any

class MemoryConfig:
    """Centralized configuration for memory management."""
    
    @staticmethod
    def get_neo4j_config(custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration with validation."""
        # Validate required environment variables
        required_env_vars = ["MEM0_API_KEY", "KUBIYA_USER_EMAIL", "KUBIYA_USER_ORG"]
        
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

        config = {
            "api_key": os.environ["MEM0_API_KEY"],
            "version": "v1.1"
        }

        # Add custom prompt if provided
        if custom_prompt:
            config["custom_prompt"] = custom_prompt

        return config

    @staticmethod
    def get_user_id() -> str:
        """Get user ID from environment variables."""
        return f"{os.environ['KUBIYA_USER_ORG']}.{os.environ['KUBIYA_USER_EMAIL']}"

    @staticmethod
    def format_memory_response(memory: Any) -> Dict[str, Any]:
        """Format memory response consistently."""
        if isinstance(memory, str):
            return {
                'content': memory,
                'memory_id': 'unknown',
                'timestamp': 'unknown',
                'metadata': {'tags': []},
                'relationships': [],
                'entities': []
            }
        elif isinstance(memory, dict):
            # Handle both old and new response formats
            return {
                'content': memory.get('content', memory.get('data', memory.get('memory', ''))),
                'memory_id': memory.get('memory_id', memory.get('id', 'unknown')),
                'timestamp': memory.get('timestamp', memory.get('created_at', 'unknown')),
                'metadata': memory.get('metadata', {'tags': []}),
                'relationships': memory.get('relationships', []),
                'entities': memory.get('extracted_entities', memory.get('entities', []))
            }
        else:
            raise ValueError(f"Unexpected memory format: {type(memory)}") 