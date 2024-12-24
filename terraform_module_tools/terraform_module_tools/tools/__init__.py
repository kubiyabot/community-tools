import logging
from typing import List, Any, Dict, Optional
from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry
from .dynamic_tool_loader import DynamicToolLoader
from ..scripts.config_loader import ConfigurationError

logger = logging.getLogger(__name__)

def initialize_tools(config: Dict[str, Any]) -> List[Tool]:
    """Initialize all Terraform tools from configuration."""
    try:
        if not config:
            raise ConfigurationError("No configuration provided")

        return DynamicToolLoader.load_tools(config)

    except Exception as e:
        logger.error(f"Failed to initialize tools: {str(e)}")
        return []

# Export necessary components
__all__ = ['initialize_tools']

# Initialize tools with dynamic config
try:
    config = tool_registry.dynamic_config
    if not config:
        logger.warning("⚠️ No dynamic configuration found")
    else:
        initialize_tools(config)
except Exception as e:
    logger.error(f"Failed to initialize tools with dynamic config: {str(e)}")