import os
from typing import Optional, Dict, Any

class MemoryConfig:
    """Centralized configuration for memory management."""
    
    @staticmethod
    def get_neo4j_config(custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Get Neo4j configuration with validation."""
        # Validate required environment variables
        required_env_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", 
                           "KUBIYA_USER_EMAIL", "KUBIYA_USER_ORG",
                           "OPENAI_API_KEY", "OPENAI_API_BASE"]
        
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

        config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "gpt-4o",
                    "temperature": 0.2,
                    "max_tokens": 1500,
                    "api_key": os.environ["OPENAI_API_KEY"],
                    "api_base": os.environ["OPENAI_API_BASE"],
                    "api_version": os.environ.get("OPENAI_API_VERSION", "2024-02-15-preview")
                }
            },
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": os.environ["NEO4J_URI"],
                    "username": os.environ["NEO4J_USER"],
                    "password": os.environ["NEO4J_PASSWORD"],
                    "database": "neo4j",
                },
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": "gpt-4o",
                        "temperature": 0.0,
                        "api_key": os.environ["OPENAI_API_KEY"],
                        "api_base": os.environ["OPENAI_API_BASE"],
                        "api_version": os.environ.get("OPENAI_API_VERSION", "2024-02-15-preview")
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
                'metadata': {'tags': []},
                'relationships': [],
                'entities': []
            }
        elif isinstance(memory, dict):
            # Handle both old and new response formats
            return {
                'content': memory.get('content', memory.get('data', memory.get('memory', ''))),
                'id': memory.get('id', memory.get('memory_id', 'unknown')),
                'timestamp': memory.get('timestamp', memory.get('created_at', 'unknown')),
                'metadata': memory.get('metadata', {'tags': []}),
                'relationships': memory.get('relationships', []),
                'entities': memory.get('extracted_entities', memory.get('entities', []))
            }
        else:
            raise ValueError(f"Unexpected memory format: {type(memory)}") 