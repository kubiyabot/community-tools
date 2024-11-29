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