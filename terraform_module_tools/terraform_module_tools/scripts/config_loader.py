import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Try to import jsonschema, but don't fail if it's not available
try:
    from jsonschema import validate
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    logger.warning("jsonschema not available - validation will be skipped")
    JSONSCHEMA_AVAILABLE = False

# JSON Schema for validation
MODULE_CONFIG_SCHEMA = {
    "type": "object",
    "patternProperties": {
        ".*": {
            "type": "object",
            "required": ["name", "description", "source", "version", "variables"],
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "source": {"type": "string"},
                "version": {"type": "string"},
                "variables": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {
                            "type": "object",
                            "required": ["type", "description"],
                            "properties": {
                                "type": {"type": "string"},
                                "description": {"type": "string"},
                                "default": {},
                                "required": {"type": "boolean"}
                            }
                        }
                    }
                }
            }
        }
    }
}

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration with fallback for missing jsonschema."""
    if not JSONSCHEMA_AVAILABLE:
        # Basic validation without jsonschema
        for module_name, module_config in config.items():
            required_fields = ["name", "description", "source", "version", "variables"]
            for field in required_fields:
                if field not in module_config:
                    raise ValueError(f"Missing required field '{field}' in module '{module_name}'")
            
            if not isinstance(module_config["variables"], dict):
                raise ValueError(f"'variables' must be an object in module '{module_name}'")
            
            for var_name, var_config in module_config["variables"].items():
                if "type" not in var_config or "description" not in var_config:
                    raise ValueError(f"Variable '{var_name}' missing required fields in module '{module_name}'")
        return True
    else:
        validate(instance=config, schema=MODULE_CONFIG_SCHEMA)
        return True

def get_module_configs() -> Dict[str, Any]:
    """Get Terraform module configurations."""
    try:
        config_path = Path(__file__).parent / 'configs' / 'module_configs.json'
        if not config_path.exists():
            logger.warning(f"No module configurations found at {config_path}")
            return {}

        with open(config_path) as f:
            configs = json.load(f)

        # Validate configuration
        validate_config(configs)
        return configs

    except Exception as e:
        logger.error(f"Failed to load module configurations: {str(e)}")
        return {} 