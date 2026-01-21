import json
import logging
from pathlib import Path
from typing import Dict, Any
from kubiya_workflow_sdk.tools.registry import tool_registry

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

def _load_from_file(config_name: str) -> Dict[str, Any]:
    """Helper function to load configuration from file."""
    config_path = Path(__file__).parent / 'configs' / f'{config_name}.json'
    if not config_path.exists():
        return {}

    with open(config_path) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file {config_name}: {str(e)}")
            return {}

def load_config(config_name: str) -> Dict[str, Any]:
    """Load and validate configuration from dynamic config or file."""
    try:
        # Get dynamic configuration
        dynamic_config = tool_registry.dynamic_config
        print(f"📝 Received dynamic configuration: {dynamic_config}")
        
        if dynamic_config:
            print("⚠️  dynamic configuration provided")
            config = dynamic_config.get(config_name, {})
            print(f"📝 Using {config_name} configuration: {config}")
        else:
            print("⚠️  No dynamic configuration provided, trying file")            
            config = _load_from_file(config_name)

        # Validate configuration if jsonschema is available and config is not empty
        if JSONSCHEMA_AVAILABLE and config:
            schema = ACCESS_CONFIG_SCHEMA if config_name == 'access_configs' else S3_CONFIG_SCHEMA
            try:
                validate(instance=config, schema=schema)
            except Exception as e:
                logger.error(f"Configuration validation failed for {config_name}: {str(e)}")
                return {}

        return config

    except Exception as e:
        logger.error(f"Error loading configuration {config_name}: {str(e)}")
        return {}

def get_access_configs() -> Dict[str, Any]:
    """Get access configurations."""
    return load_config('access_configs')

def get_s3_configs() -> Dict[str, Any]:
    """Get S3 access configurations."""
    return load_config('s3_configs')

def validate_configs():
    """Validate all configuration files exist and are valid."""
    try:
        access_configs = get_access_configs()
        s3_configs = get_s3_configs()
        
        # Return true if at least one config is present and valid
        if access_configs or s3_configs:
            return True
            
        logger.warning("No valid configurations found")
        return False
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        return False

# Export the functions
__all__ = ['get_access_configs', 'get_s3_configs', 'validate_configs']