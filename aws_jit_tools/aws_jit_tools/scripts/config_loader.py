import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

try:
    from jsonschema import validate
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    logger.warning("jsonschema not available - validation will be skipped")
    JSONSCHEMA_AVAILABLE = False

# JSON Schema for validation
ACCESS_CONFIG_SCHEMA = {
    "type": "object",
    "patternProperties": {
        ".*": {
            "type": "object",
            "required": ["name", "description", "account_id", "permission_set", "session_duration"],
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "account_id": {"type": "string"},
                "permission_set": {"type": "string"},
                "session_duration": {"type": "string", "pattern": "^PT[0-9]+[HM]$"}
            }
        }
    }
}

S3_CONFIG_SCHEMA = {
    "type": "object",
    "patternProperties": {
        ".*": {
            "type": "object",
            "required": ["name", "description", "buckets", "policy_template", "session_duration"],
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "buckets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1
                },
                "policy_template": {"type": "string", "enum": ["S3ReadOnlyPolicy", "S3FullAccessPolicy"]},
                "session_duration": {"type": "string", "pattern": "^PT[0-9]+[HM]$"}
            }
        }
    }
}

def load_config(config_name: str) -> Dict[str, Any]:
    """Load and validate configuration from JSON file."""
    try:
        config_path = Path(__file__).parent / 'configs' / f'{config_name}.json'
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path) as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in configuration file {config_name}: {str(e)}")

        # Validate configuration if jsonschema is available
        if JSONSCHEMA_AVAILABLE:
            schema = ACCESS_CONFIG_SCHEMA if config_name == 'access_configs' else S3_CONFIG_SCHEMA
            try:
                validate(instance=config, schema=schema)
            except Exception as e:
                raise ValueError(f"Configuration validation failed for {config_name}: {str(e)}")

        return config

    except Exception as e:
        logger.error(f"Error loading configuration {config_name}: {str(e)}")
        raise

def get_access_configs() -> Dict[str, Any]:
    """Get access configurations."""
    try:
        return load_config('access_configs')
    except Exception as e:
        logger.error(f"Failed to load access configurations: {str(e)}")
        return {}

def get_s3_configs() -> Dict[str, Any]:
    """Get S3 access configurations."""
    try:
        return load_config('s3_configs')
    except Exception as e:
        logger.error(f"Failed to load S3 configurations: {str(e)}")
        return {}

def validate_configs():
    """Validate all configuration files exist and are valid."""
    try:
        access_configs = get_access_configs()
        s3_configs = get_s3_configs()
        
        if not access_configs and not s3_configs:
            raise ValueError("No valid configurations found")
        
        return True
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        return False

# Export the functions
__all__ = ['get_access_configs', 'get_s3_configs', 'validate_configs'] 