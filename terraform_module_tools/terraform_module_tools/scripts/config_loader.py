import json
import logging
from pathlib import Path
from typing import Dict, Any
from jsonschema import validate

logger = logging.getLogger(__name__)

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
        validate(instance=configs, schema=MODULE_CONFIG_SCHEMA)
        return configs

    except Exception as e:
        logger.error(f"Failed to load module configurations: {str(e)}")
        return {} 