import os
from typing import Optional, Dict, Any

class MemoryConfig:
    """Centralized configuration for memory management."""
    
    @staticmethod
    def get_neo4j_config(custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Get Neo4j configuration with validation."""
        # Validate required environment variables
        required_env_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", 
                           "KUBIYA_USER_EMAIL", "KUBIYA_USER_ORG"]
        
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

        config = {
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": os.environ["NEO4J_URI"],
                    "username": os.environ["NEO4J_USER"],
                    "password": os.environ["NEO4J_PASSWORD"],
                    "database": "neo4j",  # Default Neo4j database
                    "node_properties": {
                        "Memory": ["content", "user_id", "timestamp", "metadata"],
                        "User": ["user_id", "email", "org"]
                    }
                }
            },
            "version": "v1.1"
        }

        # Add custom prompt if provided
        if custom_prompt:
            config["graph_store"]["custom_prompt"] = custom_prompt

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
                'id': 'unknown',
                'timestamp': 'unknown',
                'metadata': {'tags': []}
            }
        elif isinstance(memory, dict):
            # Handle both old and new response formats
            return {
                'content': memory.get('content', memory.get('data', memory.get('memory', ''))),
                'id': memory.get('id', memory.get('memory_id', 'unknown')),
                'timestamp': memory.get('timestamp', memory.get('created_at', 'unknown')),
                'metadata': memory.get('metadata', {'tags': []})
            }
        else:
            raise ValueError(f"Unexpected memory format: {type(memory)}") 