import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from jsonschema import validate

logger = logging.getLogger(__name__)

# Default configuration schema
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "jenkins_url": {
            "type": "string",
            "description": "Jenkins server URL"
        },
        "auth": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "password_env": {"type": "string"}
            },
            "required": ["username", "password_env"]
        },
        "jobs": {
            "type": "object",
            "properties": {
                "sync_all": {
                    "type": "boolean",
                    "default": False
                },
                "include": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "exclude": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "defaults": {
            "type": "object",
            "properties": {
                "stream_logs": {
                    "type": "boolean",
                    "default": True,
                    "description": "Stream job logs while running"
                },
                "poll_interval": {
                    "type": "integer",
                    "default": 30,
                    "description": "Interval in seconds to poll job status"
                },
                "long_running_threshold": {
                    "type": "integer",
                    "default": 300,
                    "description": "Jobs longer than this (in seconds) will be marked as long-running"
                }
            }
        }
    },
    "required": ["jenkins_url", "auth"]
}

def get_jenkins_config() -> Optional[Dict[str, Any]]:
    """Load and validate Jenkins configuration."""
    try:
        config_path = Path(__file__).parent / 'configs' / 'jenkins_config.json'
        
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return None

        with open(config_path) as f:
            config = json.load(f)

        # Validate configuration
        validate(instance=config, schema=CONFIG_SCHEMA)

        # Set default values
        if 'defaults' not in config:
            config['defaults'] = {}
        config['defaults'].setdefault('stream_logs', True)
        config['defaults'].setdefault('poll_interval', 30)
        config['defaults'].setdefault('long_running_threshold', 300)

        return config

    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        return None 