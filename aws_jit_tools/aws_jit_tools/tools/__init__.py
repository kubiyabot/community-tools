import logging
from kubiya_sdk.tools.registry import tool_registry
from .base import AWSJITTool
from . import jit_access

logger = logging.getLogger(__name__)

def initialize_tools():
    """Initialize and register all JIT access tools."""
    try:
        logger.info("Initializing AWS JIT access tools...")
        # Get all tools from jit_access module
        return list(jit_access.tools.values())
    except Exception as e:
        logger.error(f"Failed to initialize tools: {str(e)}")
        raise

__all__ = ['initialize_tools', 'AWSJITTool']
