import logging
from .tools import initialize_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize():
    """Initialize Terraform module tools using dynamic configuration."""
    try:
        logger.info("Starting Terraform module tools initialization...")
        initialized_tools = initialize_tools()
        if not initialized_tools:
            error_msg = "No tools were initialized"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        logger.info(f"Successfully initialized {len(initialized_tools)} Terraform tools")
        return initialized_tools
    except Exception as e:
        error_msg = f"Failed to initialize Terraform tools: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

# Initialize tools when module is imported and store them
try:
    tools = initialize()
except Exception as e:
    logger.error(f"Failed to initialize tools: {str(e)}")
    tools = []

# Export the tools and initialization function
__all__ = ['tools', 'initialize']
