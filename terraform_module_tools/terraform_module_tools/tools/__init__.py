import logging
from .module_tools import tools, initialize_module_tools

logger = logging.getLogger(__name__)

def initialize_tools():
    """Initialize and register all Terraform module tools."""
    try:
        logger.info("Initializing Terraform module tools...")
        return list(tools.values())
    except Exception as e:
        logger.error(f"Failed to initialize tools: {str(e)}")
        raise

__all__ = ['initialize_tools', 'tools']