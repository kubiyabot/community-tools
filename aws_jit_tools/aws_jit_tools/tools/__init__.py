import logging
from kubiya_sdk.tools.registry import tool_registry
from .base import AWSJITTool
from . import jit_access

logger = logging.getLogger(__name__)

def initialize_tools():
    """Initialize and register all JIT access tools."""
    try:
        logger.info("Initializing AWS JIT access tools...")
        # Tools are automatically registered when jit_access module is imported
        return [
            jit_access.se_access,
            jit_access.admin_access,
            jit_access.developer_access
        ]
    except Exception as e:
        logger.error(f"Failed to initialize tools: {str(e)}")
        raise

__all__ = ['initialize_tools', 'AWSJITTool']
