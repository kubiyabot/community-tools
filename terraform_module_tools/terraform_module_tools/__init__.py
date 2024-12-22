import logging
from .tools import initialize_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize(dynamic_config=None):
    """Initialize Terraform module tools using dynamic configuration."""
    try:
        logger.info("Starting Terraform module tools initialization...")
        if not dynamic_config:
            logger.warning("No dynamic configuration provided")
            return []
            
        # Pass the dynamic config directly to initialize_tools
        initialized_tools = initialize_tools(dynamic_config)
        if initialized_tools:
            logger.info(f"Successfully initialized {len(initialized_tools)} Terraform tools")
            return initialized_tools
        else:
            logger.warning("No tools were initialized")
            return []
    except Exception as e:
        error_msg = f"Failed to initialize Terraform tools: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

# Export the initialization function
__all__ = ['initialize']
